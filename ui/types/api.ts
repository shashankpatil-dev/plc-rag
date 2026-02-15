/**
 * TypeScript types matching the backend Pydantic models
 */

export enum ConditionType {
  YES = "Yes",
  NO = "No",
  NO_YES = "No/Yes"
}

export interface State {
  step: number
  description: string
  interlocks: string[]
  condition: ConditionType
  next_step: number
}

export interface MachineLogic {
  name: string
  states: State[]
  state_count?: number
  all_interlocks?: string[]
  total_interlock_count?: number
  cycle_path?: number[]
}

export interface ParsedCSV {
  machines: MachineLogic[]
  total_machines: number
  total_states?: number
  all_interlocks?: string[]
  machine_names?: string[]
}

export interface UploadResponse {
  status: string
  message: string
  filename?: string
  parsed_data?: ParsedCSV
}
