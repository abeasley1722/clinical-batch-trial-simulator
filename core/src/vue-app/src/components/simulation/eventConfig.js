export const EVENT_TYPES = [
  { value: 'pathology', label: '🦠 Pathology' },
  { value: 'intubate', label: '💉 Intubate' },
  { value: 'start_vent', label: '🌬️ Start Vent' },
  { value: 'change_vent', label: '🔧 Change Vent' },
  { value: 'bolus', label: '💊 Drug Bolus' },
  { value: 'infusion', label: '💉 Infusion' },
  { value: 'exercise', label: '🏃 Exercise' }
]

export function getDefaultParams(type) {
  switch (type) {
    case 'pathology':
      return { type: 'ARDS', severity: 0.5 }

    case 'start_vent':
    case 'change_vent':
      return { fio2: 40, peep: 5, rr: 14, vt: 420 }

    case 'bolus':
      return { drug: 'Fentanyl', dose: 100, unit: 'ug' }

    case 'infusion':
      return { drug: 'Propofol', rate: 100 }

    case 'exercise':
      return { intensity: 0.1, duration: 5 }

    default:
      return {}
  }
}