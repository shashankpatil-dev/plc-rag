'use client'

import { ParsedCSV, MachineLogic, State } from '@/types/api'

interface LogicViewerProps {
  parsedData: ParsedCSV
}

export default function LogicViewer({ parsedData }: LogicViewerProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-8 mt-6">
      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
        Parsed Logic Sheets
      </h3>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
          <div className="text-sm text-blue-600 dark:text-blue-400">Total Machines</div>
          <div className="text-2xl font-bold text-blue-900 dark:text-blue-100">
            {parsedData.total_machines}
          </div>
        </div>
        <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
          <div className="text-sm text-green-600 dark:text-green-400">Total States</div>
          <div className="text-2xl font-bold text-green-900 dark:text-green-100">
            {parsedData.total_states}
          </div>
        </div>
        <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
          <div className="text-sm text-purple-600 dark:text-purple-400">Unique Interlocks</div>
          <div className="text-2xl font-bold text-purple-900 dark:text-purple-100">
            {parsedData.all_interlocks?.length || 0}
          </div>
        </div>
      </div>

      {/* Machines */}
      <div className="space-y-6">
        {parsedData.machines.map((machine, idx) => (
          <MachineCard key={idx} machine={machine} />
        ))}
      </div>
    </div>
  )
}

function MachineCard({ machine }: { machine: MachineLogic }) {
  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
          {machine.name}
        </h4>
        <div className="flex gap-3 text-sm">
          <span className="text-gray-600 dark:text-gray-400">
            {machine.state_count} states
          </span>
          <span className="text-gray-600 dark:text-gray-400">
            {machine.total_interlock_count} interlocks
          </span>
        </div>
      </div>

      {/* State Cycle Path */}
      <div className="mb-4">
        <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">State Cycle:</div>
        <div className="flex items-center gap-2 flex-wrap">
          {machine.cycle_path?.map((step, idx) => (
            <span key={idx} className="inline-flex items-center gap-1">
              <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-sm font-mono">
                {step}
              </span>
              {idx < machine.cycle_path!.length - 1 && (
                <span className="text-gray-400">→</span>
              )}
            </span>
          ))}
        </div>
      </div>

      {/* States Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                Step
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                Description
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                Interlocks
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                Condition
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                Next Step
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {machine.states.map((state, idx) => (
              <StateRow key={idx} state={state} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function StateRow({ state }: { state: State }) {
  return (
    <tr className="hover:bg-gray-50 dark:hover:bg-gray-750">
      <td className="px-3 py-2 whitespace-nowrap text-sm font-mono text-gray-900 dark:text-gray-100">
        {state.step}
      </td>
      <td className="px-3 py-2 text-sm text-gray-700 dark:text-gray-300">
        {state.description}
      </td>
      <td className="px-3 py-2 text-sm">
        {state.interlocks && state.interlocks.length > 0 ? (
          <div className="flex flex-wrap gap-1">
            {state.interlocks.map((interlock, idx) => (
              <span
                key={idx}
                className="inline-block px-2 py-0.5 bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200 rounded text-xs font-mono"
              >
                {interlock}
              </span>
            ))}
          </div>
        ) : (
          <span className="text-gray-400 dark:text-gray-600 text-xs">none</span>
        )}
      </td>
      <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
        <span className="inline-block px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs">
          {state.condition}
        </span>
      </td>
      <td className="px-3 py-2 whitespace-nowrap text-sm font-mono text-gray-900 dark:text-gray-100">
        {state.next_step}
      </td>
    </tr>
  )
}
