// Work Order Management Component

'use client'

import { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { Wrench, Clock, User, Calendar, CheckCircle, AlertCircle, ExternalLink, PlayCircle, XCircle, X, FileText, Camera, MessageSquare } from 'lucide-react'
import type { WorkOrder } from '@/types'

interface WorkOrderListProps {
  workOrders: WorkOrder[];
}

interface ModalState {
  isOpen: boolean;
  type: 'details' | 'start' | 'complete' | null;
  workOrder: WorkOrder | null;
}

export default function WorkOrderList({ workOrders }: WorkOrderListProps) {
  const [modal, setModal] = useState<ModalState>({ isOpen: false, type: null, workOrder: null })
  const [hoursWorked, setHoursWorked] = useState('')
  const [completionNotes, setCompletionNotes] = useState('')

  const openModal = (type: 'details' | 'start' | 'complete', workOrder: WorkOrder) => {
    setModal({ isOpen: true, type, workOrder })
    setHoursWorked('')
    setCompletionNotes('')
  }

  const closeModal = () => {
    setModal({ isOpen: false, type: null, workOrder: null })
  }

  const handleStartWork = () => {
    // In real app: API call to update status
    alert(`Started work on: ${modal.workOrder?.title}\nStatus changed to IN_PROGRESS`)
    closeModal()
  }

  const handleCompleteWork = () => {
    if (!hoursWorked) {
      alert('Please enter hours worked')
      return
    }
    // In real app: API call to complete work order
    alert(`Work order completed!\nHours: ${hoursWorked}\nNotes: ${completionNotes || 'None'}`)
    closeModal()
  }

  if (!workOrders || workOrders.length === 0) {
    return (
      <div className="text-center py-8">
        <Wrench className="w-12 h-12 text-slate-700 mx-auto mb-3" />
        <p className="text-slate-500">No work orders</p>
        <p className="text-sm text-slate-600 mt-1">All maintenance tasks completed</p>
      </div>
    )
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'HIGH': return { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-500', badge: 'bg-red-500' }
      case 'MEDIUM': return { bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', text: 'text-yellow-500', badge: 'bg-yellow-500' }
      case 'LOW': return { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-500', badge: 'bg-blue-500' }
      default: return { bg: 'bg-slate-500/10', border: 'border-slate-500/30', text: 'text-slate-500', badge: 'bg-slate-500' }
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED': return 'text-emerald-500'
      case 'IN_PROGRESS': return 'text-blue-500'
      case 'OPEN': return 'text-yellow-500'
      case 'SCHEDULED': return 'text-slate-500'
      default: return 'text-slate-500'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED': return <CheckCircle className="w-4 h-4" />
      case 'IN_PROGRESS': return <Clock className="w-4 h-4 animate-pulse" />
      case 'OPEN': return <AlertCircle className="w-4 h-4" />
      default: return <Calendar className="w-4 h-4" />
    }
  }

  return (
    <>
      {/* Modal Overlay */}
      {modal.isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-200">
          {/* Glassy Background */}
          <div 
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={closeModal}
          />
          
          {/* Modal Content */}
          <div className="relative w-full max-w-lg bg-slate-900/95 backdrop-blur-xl border border-slate-700 rounded-xl sm:rounded-2xl shadow-2xl animate-in zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between p-4 sm:p-6 border-b border-slate-800 sticky top-0 bg-slate-900/95 backdrop-blur-xl z-10">
              <h3 className="text-base sm:text-lg font-semibold text-white flex items-center gap-2">
                {modal.type === 'details' && <><FileText className="w-4 h-4 sm:w-5 sm:h-5" /> Details</>}
                {modal.type === 'start' && <><PlayCircle className="w-4 h-4 sm:w-5 sm:h-5" /> Start Work</>}
                {modal.type === 'complete' && <><CheckCircle className="w-4 h-4 sm:w-5 sm:h-5" /> Complete</>}
              </h3>
              <button
                onClick={closeModal}
                className="p-1.5 sm:p-2 hover:bg-slate-800 rounded-lg transition-colors"
              >
                <X className="w-4 h-4 sm:w-5 sm:h-5 text-slate-400" />
              </button>
            </div>

            {/* Body */}
            <div className="p-4 sm:p-6 space-y-3 sm:space-y-4">
              {/* Work Order Info */}
              <div className="space-y-2 sm:space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-slate-500">{modal.workOrder?.id}</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(modal.workOrder?.priority || '').badge} text-white`}>
                    {modal.workOrder?.priority}
                  </span>
                </div>
                <h4 className="text-lg sm:text-xl font-bold text-white break-words">{modal.workOrder?.title}</h4>
                <p className="text-xs sm:text-sm text-slate-400">{modal.workOrder?.description}</p>
              </div>

              {/* Details View */}
              {modal.type === 'details' && (
                <div className="space-y-3 sm:space-y-4 pt-3 sm:pt-4 border-t border-slate-800">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                    <div>
                      <p className="text-xs text-slate-500 mb-1">Assigned To</p>
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4 text-slate-400" />
                        <p className="text-sm text-white">{modal.workOrder?.assigned_to}</p>
                      </div>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 mb-1">Status</p>
                      <p className="text-sm text-white">{modal.workOrder?.status.replace('_', ' ')}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 mb-1">Category</p>
                      <div className="flex items-center gap-2">
                        <Wrench className="w-4 h-4 text-slate-400" />
                        <p className="text-sm text-white">{modal.workOrder?.category}</p>
                      </div>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 mb-1">Estimated Time</p>
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-slate-400" />
                        <p className="text-sm text-white">{modal.workOrder?.estimated_hours}h</p>
                      </div>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 mb-1">Due Date</p>
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-slate-400" />
                      <p className="text-sm text-white">
                        {modal.workOrder?.due_date && formatDistanceToNow(new Date(modal.workOrder.due_date), { addSuffix: true })}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Start Work View */}
              {modal.type === 'start' && (
                <div className="space-y-3 sm:space-y-4 pt-3 sm:pt-4 border-t border-slate-800">
                  <div className="p-3 sm:p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
                    <p className="text-xs sm:text-sm text-emerald-400">
                      Ready to start this work order? This will:
                    </p>
                    <ul className="mt-2 space-y-1 text-xs sm:text-sm text-emerald-300">
                      <li>• Change status to IN_PROGRESS</li>
                      <li>• Start time tracking</li>
                      <li>• Notify assigned technician</li>
                      <li>• Log activity in system</li>
                    </ul>
                  </div>
                </div>
              )}

              {/* Complete Work View */}
              {modal.type === 'complete' && (
                <div className="space-y-3 sm:space-y-4 pt-3 sm:pt-4 border-t border-slate-800">
                  <div>
                    <label className="block text-xs sm:text-sm font-medium text-white mb-2">
                      Actual Hours Worked *
                    </label>
                    <input
                      type="number"
                      step="0.5"
                      value={hoursWorked}
                      onChange={(e) => setHoursWorked(e.target.value)}
                      placeholder="e.g., 3.5"
                      className="w-full px-3 sm:px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <p className="text-xs text-slate-500 mt-1">
                      Estimated: {modal.workOrder?.estimated_hours}h
                    </p>
                  </div>
                  <div>
                    <label className="block text-xs sm:text-sm font-medium text-white mb-2">
                      Completion Notes
                    </label>
                    <textarea
                      value={completionNotes}
                      onChange={(e) => setCompletionNotes(e.target.value)}
                      placeholder="Describe work performed, parts replaced, observations..."
                      rows={3}
                      className="w-full px-3 sm:px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 p-4 sm:p-6 border-t border-slate-800 sticky bottom-0 bg-slate-900/95 backdrop-blur-xl">
              <button
                onClick={closeModal}
                className="flex-1 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors font-medium text-sm sm:text-base"
              >
                Cancel
              </button>
              {modal.type === 'start' && (
                <button
                  onClick={handleStartWork}
                  className="flex-1 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition-colors font-medium flex items-center justify-center gap-2 text-sm sm:text-base"
                >
                  <PlayCircle className="w-4 h-4" />
                  Start Work
                </button>
              )}
              {modal.type === 'complete' && (
                <button
                  onClick={handleCompleteWork}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors font-medium flex items-center justify-center gap-2 text-sm sm:text-base"
                >
                  <CheckCircle className="w-4 h-4" />
                  Complete
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Work Orders List */}
      <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
        {workOrders.map((order) => {
        const priorityColors = getPriorityColor(order.priority)
        const statusColor = getStatusColor(order.status)

        return (
          <div
            key={order.id}
            className={`p-4 rounded-lg border ${priorityColors.bg} ${priorityColors.border} transition-all hover:scale-[1.02]`}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-slate-400">{order.id}</span>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${priorityColors.badge} text-white`}>
                  {order.priority}
                </span>
              </div>
              <div className={`flex items-center gap-1 ${statusColor}`}>
                {getStatusIcon(order.status)}
                <span className="text-xs font-medium">{order.status.replace('_', ' ')}</span>
              </div>
            </div>

            <h4 className="text-sm font-semibold text-white mb-1">{order.title}</h4>
            <p className="text-xs text-slate-400 mb-3 line-clamp-2">{order.description}</p>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center gap-1 text-slate-500">
                <User className="w-3 h-3" />
                <span>{order.assigned_to}</span>
              </div>
              <div className="flex items-center gap-1 text-slate-500">
                <Clock className="w-3 h-3" />
                <span>{order.estimated_hours}h estimated</span>
              </div>
              <div className="flex items-center gap-1 text-slate-500">
                <Calendar className="w-3 h-3" />
                <span>Due {formatDistanceToNow(new Date(order.due_date), { addSuffix: true })}</span>
              </div>
              <div className="flex items-center gap-1 text-slate-500">
                <Wrench className="w-3 h-3" />
                <span>{order.category}</span>
              </div>
            </div>

            {order.status === 'COMPLETED' && order.actual_hours && (
              <div className="mt-2 pt-2 border-t border-slate-700">
                <span className="text-xs text-emerald-500">
                  ✓ Completed in {order.actual_hours}h (vs {order.estimated_hours}h estimated)
                </span>
              </div>
            )}

            {/* Action Buttons */}
            <div className="mt-3 pt-3 border-t border-slate-700/50 flex gap-2">
              <button
                onClick={() => openModal('details', order)}
                className="flex-1 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs font-medium transition-colors flex items-center justify-center gap-1"
              >
                <ExternalLink className="w-3 h-3" />
                View Details
              </button>
              
              {order.status === 'OPEN' && (
                <button
                  onClick={() => openModal('start', order)}
                  className="flex-1 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-medium transition-colors flex items-center justify-center gap-1"
                >
                  <PlayCircle className="w-3 h-3" />
                  Start Work
                </button>
              )}
              
              {order.status === 'IN_PROGRESS' && (
                <button
                  onClick={() => openModal('complete', order)}
                  className="flex-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-medium transition-colors flex items-center justify-center gap-1"
                >
                  <CheckCircle className="w-3 h-3" />
                  Complete
                </button>
              )}
            </div>
          </div>
        )
      })}
      </div>
    </>
  )
}
