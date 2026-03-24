
# === BATCH MODE SUPPORT ===
batches = {}
batch_lock = threading.Lock()
batch_cancel_flags = {}  # batch_id -> True if should cancel (for thread-level check)



def run_batch_thread(batch_id, batch):
    """
    Run a batch of patients in parallel using multiprocessing.Pool.

    Uses imap_unordered for better progress visibility - results are
    yielded as each patient completes rather than waiting for all.

    Supports replicates: if replicates > 1, each patient is run multiple times
    with output files suffixed _r1, _r2, etc.
    """
    print(f"[BATCH] run_batch_thread started for {batch_id}")

    patient_count = batch.get('patient_count', 0) #TODO: verify json body field name
    patient_count = 5 #TODO: Temporary override for testing - remove when database integration is done   
    patients = []
    #TODO: draw patients from database
    """
    patients += draw_patients_from_database(criteria, count=patient_count)
    patient_count -= len(patients)

    """

    #generate patients if not enough patients in database match criteria
    generator = SoldierGenerator('random') #TODO: expand to take demographic criteria from batch config, better random seed?
    generated_patients = generator.generate_cohort(patient_count)

    # Stabilize patients in parallel
    num_workers = args.workers or max(1, os.cpu_count() - 1)
    print(f"\nStabilizing {len(generated_patients)} patients with {num_workers} workers...")
    print(f"Estimated time: {len(generated_patients) * 2.5 / num_workers:.0f}-{len(generated_patients) * 3.5 / num_workers:.0f} minutes\n")
    
    # Prepare arguments for worker processes
    #TODO: edit output_dir to database output path when database integration is done
    output_dir = os.path.join(RESULTS_FOLDER, f"batch_{batch_id}_output")
    work_items = [
        (asdict(profile), output_dir, PULSE_BIN, PULSE_PYTHON)
        for profile in generated_patients
    ]
    
    # Run stabilization
    from multiprocessing import freeze_support
    freeze_support()
    
    results = []
    completed = 0
    failed = 0
    
    #TODO: verify stabilize_patient is working as intended and saves data to database properly
    with ProcessPool(num_workers) as pool:
        for result in pool.imap_unordered(stabilize_patient, work_items):
            completed += 1
            if result['status'] == 'success':
                print(f"  [{completed}/{len(generated_patients)}] ✓ {result['name']}")
            else:
                failed += 1
                print(f"  [{completed}/{len(generated_patients)}] ✗ {result['name']}: {result.get('message', 'Unknown error')}")
            results.append(result)

    #add generated patients to cohort
    patients += [r['name'] for r in results if r['status'] == 'success']

    #generate experiment object
    experiment = Experiment.from_json(batch, patients)

    #TODO: remove when Experiment object integration is done
    pre_stabilized = batch.get('patients', [])
    custom_patients = batch.get('custom_patients', [])  # List of {name, json}
    duration_s = batch.get('duration_s', 300)
    workers = batch.get('workers', max(1, (os.cpu_count() or 4) - 1))
    replicates = max(1, batch.get('replicates', 1))

    base_patient_count = len(pre_stabilized) + len(custom_patients)
    total_jobs = base_patient_count * replicates
    print(f"[BATCH] {batch_id}: {base_patient_count} patients x {replicates} replicates = {total_jobs} jobs")
    
    if base_patient_count == 0:
        with batch_lock:
            batches[batch_id]['status'] = 'error'
            batches[batch_id]['message'] = 'No patients selected'
        print(f"[BATCH] {batch_id}: No patients selected!")
        return

    # Cap workers at CPU count and total job count
    max_workers = os.cpu_count() or 4
    workers = min(workers, max_workers, total_jobs) if total_jobs > 0 else 1

    # Initialize job progress tracking (patient x replicate combinations)
    with batch_lock:
        batches[batch_id]['replicates'] = replicates
        batches[batch_id]['base_patient_count'] = base_patient_count
        batches[batch_id]['total_jobs'] = total_jobs

        # Pre-stabilized patients x replicates
        for p in pre_stabilized:
            for rep in range(1, replicates + 1):
                job_id = f"{p}_r{rep}" if replicates > 1 else p
                batches[batch_id]['patients'][job_id] = {
                    'status': 'queued',
                    'sim_time': 0,
                    'duration': duration_s,
                    'is_custom': False,
                    'replicate': rep,
                    'base_patient': p
                }
        # Custom patients x replicates
        for cp in custom_patients:
            for rep in range(1, replicates + 1):
                job_id = f"custom_{cp['name']}_r{rep}" if replicates > 1 else f"custom_{cp['name']}"
                batches[batch_id]['patients'][job_id] = {
                    'status': 'queued',
                    'sim_time': 0,
                    'duration': duration_s,
                    'is_custom': True,
                    'replicate': rep,
                    'base_patient': cp['name']
                }
        batches[batch_id]['workers'] = workers
    
    try:
        # Create output directory
        timestamp = experiment.experiment_id  # Use experiment ID as timestamp for better traceability
        batch_dir = os.path.join(RESULTS_FOLDER, f"batch_{batch_id}_{timestamp}")
        os.makedirs(batch_dir, exist_ok=True)
        
        # Prepare batch config (without patients list)
        # Include PULSE_BIN and PULSE_PYTHON so worker processes know where to chdir and import from
        # v6: start_intubated defaults to False - use events for intubation/ventilation
        batch_config = {
            'batch_id': batch_id,  # For HTTP controller concurrent identification
            'duration_s': duration_s,
            'sample_rate_hz': batch.get('sample_rate_hz', 50),
            'start_intubated': batch.get('start_intubated', False),
            'vent_settings': batch.get('vent_settings', {}),
            'events': batch.get('events', []),
            'pulse_bin': PULSE_BIN,
            'pulse_python': PULSE_PYTHON,
            'output_columns': batch.get('output_columns'),
            'available_variables': AVAILABLE_VARIABLES,
        }

        # Clear any stale cancel flag for this batch (file-based)
        clear_batch_cancel_flag(batch_id)

        # Create argument tuples for each patient x replicate combination
        # Pre-stabilized: pass filename string
        # Custom: pass dict with {name, json}
        # Include replicate info for file naming
        # Cancellation is checked via file-based flag, not passed in args
        #TODO: use experiment object?
        patient_args = []
        for p in patients:
            #TODO: add in replicates if needed
            job_id = p
            config = batch_config.copy() #TODO: use experiment object?
            patient_args.append((p, config, batch_dir, job_id))
        """
        for p in pre_stabilized:
            for rep in range(1, replicates + 1):
                job_id = f"{p}_r{rep}" if replicates > 1 else p
                config_with_rep = batch_config.copy()
                config_with_rep['replicate'] = rep
                config_with_rep['replicate_suffix'] = f"_r{rep}" if replicates > 1 else ""
                patient_args.append((p, config_with_rep, batch_dir, job_id))
        for cp in custom_patients:
            for rep in range(1, replicates + 1):
                job_id = f"custom_{cp['name']}_r{rep}" if replicates > 1 else f"custom_{cp['name']}"
                config_with_rep = batch_config.copy()
                config_with_rep['replicate'] = rep
                config_with_rep['replicate_suffix'] = f"_r{rep}" if replicates > 1 else ""
                patient_args.append((cp, config_with_rep, batch_dir, job_id))
        """

        # Run with ProcessPool using apply_async for non-blocking cancellation support
        print(f"Starting batch {batch_id} with {workers} workers for {total_jobs} jobs "
              f"({base_patient_count} patients x {replicates} replicates)")

        csv_paths = {}
        completed = 0
        cancelled = False

        with ProcessPool(processes=workers) as pool:
            # Submit all jobs asynchronously
            async_results = []
            #TODO: use experiment object?
            for args in patient_args:
                async_results.append(pool.apply_async(run_single_patient, (args,)))

            # Poll for results with periodic cancel checks
            pending_results = list(enumerate(async_results))
            cancel_grace_period_start = None
            CANCEL_GRACE_PERIOD_S = 15  # Give workers 15 seconds to save partial results

            while pending_results:
                # Check for cancellation every iteration (roughly every 0.5s)
                if batch_cancel_flags.get(batch_id):
                    if cancel_grace_period_start is None:
                        # First time noticing cancellation - start grace period
                        cancel_grace_period_start = time.time()
                        print(f"[BATCH] Cancellation requested for {batch_id}, waiting up to {CANCEL_GRACE_PERIOD_S}s for {len(pending_results)} jobs to save partial results...")
                    elif time.time() - cancel_grace_period_start > CANCEL_GRACE_PERIOD_S:
                        # Grace period expired - force terminate
                        print(f"[BATCH] Grace period expired, terminating {len(pending_results)} remaining jobs...")
                        pool.terminate()
                        cancelled = True
                        break

                # Check each pending result with a short timeout
                still_pending = []
                for idx, async_result in pending_results:
                    try:
                        # Try to get result with short timeout
                        result = async_result.get(timeout=0.1)

                        # Process the result
                        job_id = result['job_id']
                        status = result['status']

                        with batch_lock:
                            if job_id in batches[batch_id]['patients']:
                                batches[batch_id]['patients'][job_id]['status'] = status
                                if status == 'complete':
                                    batches[batch_id]['patients'][job_id]['csv_path'] = result['csv_path']
                                    batches[batch_id]['patients'][job_id]['sim_time'] = result['duration']
                                    csv_paths[job_id] = result['csv_path']
                                elif status == 'cancelled':
                                    batches[batch_id]['patients'][job_id]['message'] = result.get('message', 'Cancelled')
                                    if result.get('csv_path'):
                                        csv_paths[job_id] = result['csv_path']
                                    print(f"[BATCH] Job {job_id} saved partial results: {result.get('message', '')}")
                                else:
                                    batches[batch_id]['patients'][job_id]['message'] = result.get('message', 'Unknown error')
                                    print(f"[ERROR] Job {job_id} failed:")
                                    print(f"  Message: {result.get('message', 'Unknown')}")
                                    if 'traceback' in result:
                                        print(f"  Traceback:\n{result['traceback']}")

                        completed += 1
                        print(f"Batch {batch_id}: {result.get('patient_name', job_id)} {status} ({completed}/{total_jobs})")

                    except MPTimeoutError:
                        # Result not ready yet, keep it in pending list
                        still_pending.append((idx, async_result))
                    except Exception as e:
                        # Job raised an exception
                        completed += 1
                        import traceback
                        print(f"[ERROR] Job raised exception: {e}")
                        print(f"[ERROR] Traceback: {traceback.format_exc()}")

                pending_results = still_pending

                # If we're in grace period and all jobs have finished, we're done
                if cancel_grace_period_start is not None and not pending_results:
                    cancelled = True
                    print(f"[BATCH] All jobs saved partial results")
                    break

                # Small sleep to prevent busy-waiting
                if pending_results:
                    time.sleep(0.1)

        # Clean up cancel flags (both thread-level and file-based)
        if batch_id in batch_cancel_flags:
            del batch_cancel_flags[batch_id]
        clear_batch_cancel_flag(batch_id)

        # Create ZIP of all results (complete or partial from cancelled jobs)
        # Even if cancelled, include whatever we collected
        if csv_paths:
            zip_path = os.path.join(RESULTS_FOLDER, f"batch_{batch_id}_{timestamp}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for job_id, csv_path in csv_paths.items():
                    zf.write(csv_path, os.path.basename(csv_path))

            with batch_lock:
                batches[batch_id]['status'] = 'cancelled' if cancelled else 'complete'
                batches[batch_id]['zip_path'] = zip_path
                batches[batch_id]['batch_dir'] = batch_dir
                batches[batch_id]['completed_count'] = len(csv_paths)
                batches[batch_id]['total_count'] = total_jobs

            status_msg = "cancelled" if cancelled else "complete"
            print(f"Batch {batch_id} {status_msg}: {len(csv_paths)}/{total_jobs} jobs have results")
        else:
            # No results at all (very early cancellation or all jobs failed)
            with batch_lock:
                batches[batch_id]['status'] = 'cancelled' if cancelled else 'failed'
                batches[batch_id]['completed_count'] = 0
                batches[batch_id]['total_count'] = total_jobs
            print(f"Batch {batch_id} {'cancelled' if cancelled else 'failed'}: no results collected")
    
    except Exception as e:
        import traceback
        with batch_lock:
            batches[batch_id]['status'] = 'error'
            batches[batch_id]['message'] = str(e)
            batches[batch_id]['traceback'] = traceback.format_exc()
        print(f"Batch {batch_id} failed: {e}")

def get_cancel_flag_path(batch_id):
    """Get the path to the cancel flag file for a batch.

    Uses os.path.realpath() to normalize the temp directory path,
    ensuring consistency between main process and worker processes
    (Windows can return short 8.3 paths vs long paths depending on context).
    """
    temp_dir = os.path.realpath(tempfile.gettempdir())
    return os.path.join(temp_dir, f"pulse_batch_cancel_{batch_id}.flag")

def set_batch_cancel_flag(batch_id):
    """Set the cancel flag for a batch by creating a flag file."""
    flag_path = get_cancel_flag_path(batch_id)
    try:
        with open(flag_path, 'w') as f:
            f.write('cancel')
        # Also get the absolute/real path to verify
        real_path = os.path.realpath(flag_path)
        print(f"[BATCH] Cancel flag file created: {flag_path}")
        if real_path != flag_path:
            print(f"[BATCH] Real path: {real_path}")
        return True
    except Exception as e:
        print(f"[BATCH] Failed to create cancel flag file: {e}")
        return False

def check_batch_cancel_flag(batch_id):
    """Check if the cancel flag is set for a batch."""
    flag_path = get_cancel_flag_path(batch_id)
    return os.path.exists(flag_path)

def clear_batch_cancel_flag(batch_id):
    """Clear the cancel flag for a batch by removing the flag file."""
    flag_path = get_cancel_flag_path(batch_id)
    try:
        if os.path.exists(flag_path):
            os.remove(flag_path)
    except Exception:
        pass  # Ignore errors during cleanup
