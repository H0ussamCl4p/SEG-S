'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Plus, Wifi, Database } from 'lucide-react'
import { mutate } from 'swr'
import { apiUrl } from '@/lib/api-config'

interface AddEquipmentDialogProps {
  onSuccess?: () => void
}

export default function AddEquipmentDialog({ onSuccess }: AddEquipmentDialogProps) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    id: '',
    name: '',
    type: 'Motor',
    location: '',
    mqtt_topic: 'factory/plc/data',
    status: 'ONLINE'
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await fetch(apiUrl('/api/equipment'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })

      if (!response.ok) {
        const error = await response.json()
        alert(`Error: ${error.detail || 'Failed to add equipment'}`)
        setLoading(false)
        return
      }

      const result = await response.json()
      
      // Show MQTT connection info
      alert(
        `✅ Equipment Added Successfully!\n\n` +
        `Equipment ID: ${result.equipment.id}\n` +
        `MQTT Broker: ${result.mqtt_info.broker}\n` +
        `Topic: ${result.mqtt_info.topic}\n\n` +
        `Configure your ESP32 to publish data to this topic.`
      )

      // Refresh equipment list
      mutate(apiUrl('/api/equipment'))
      
      // Reset form and close dialog
      setFormData({
        id: '',
        name: '',
        type: 'Motor',
        location: '',
        mqtt_topic: 'factory/plc/data',
        status: 'ONLINE'
      })
      setOpen(false)
      onSuccess?.()
    } catch (error) {
      alert('Failed to add equipment. Check console for details.')
      console.error('Add equipment error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="bg-blue-600 hover:bg-blue-700">
          <Plus className="w-4 h-4 mr-2" />
          Add Equipment
        </Button>
      </DialogTrigger>
      <DialogContent className="bg-slate-900 border-slate-800 text-white max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Wifi className="w-5 h-5 text-blue-400" />
            Connect New Equipment (ESP32/PLC)
          </DialogTitle>
          <DialogDescription className="text-slate-400">
            Register equipment connected via ESP32 MQTT bridge. The system will automatically monitor data from the configured topic.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Equipment ID */}
          <div>
            <Label htmlFor="id" className="text-slate-300">
              Equipment ID <span className="text-red-400">*</span>
            </Label>
            <Input
              id="id"
              value={formData.id}
              onChange={(e) => setFormData({ ...formData, id: e.target.value.toUpperCase() })}
              placeholder="e.g., PLC_001, ESP32_MOTOR_01"
              className="bg-slate-800 border-slate-700 text-white"
              required
            />
            <p className="text-xs text-slate-500 mt-1">Unique identifier for this equipment</p>
          </div>

          {/* Equipment Name */}
          <div>
            <Label htmlFor="name" className="text-slate-300">
              Equipment Name <span className="text-red-400">*</span>
            </Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Assembly Line Robot, Cooling Fan"
              className="bg-slate-800 border-slate-700 text-white"
              required
            />
          </div>

          {/* Type and Location */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="type" className="text-slate-300">
                Type <span className="text-red-400">*</span>
              </Label>
              <Select value={formData.type} onValueChange={(value) => setFormData({ ...formData, type: value })}>
                <SelectTrigger className="bg-slate-800 border-slate-700 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800">
                  <SelectItem value="Motor" className="text-white">Motor</SelectItem>
                  <SelectItem value="Pump" className="text-white">Pump</SelectItem>
                  <SelectItem value="Conveyor" className="text-white">Conveyor</SelectItem>
                  <SelectItem value="Press" className="text-white">Press</SelectItem>
                  <SelectItem value="Robot" className="text-white">Robot</SelectItem>
                  <SelectItem value="Fan" className="text-white">Fan</SelectItem>
                  <SelectItem value="Compressor" className="text-white">Compressor</SelectItem>
                  <SelectItem value="Other" className="text-white">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="location" className="text-slate-300">
                Location <span className="text-red-400">*</span>
              </Label>
              <Input
                id="location"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                placeholder="e.g., Line A, Building 2"
                className="bg-slate-800 border-slate-700 text-white"
                required
              />
            </div>
          </div>

          {/* MQTT Topic */}
          <div>
            <Label htmlFor="mqtt_topic" className="text-slate-300 flex items-center gap-2">
              <Database className="w-4 h-4" />
              MQTT Topic <span className="text-red-400">*</span>
            </Label>
            <Input
              id="mqtt_topic"
              value={formData.mqtt_topic}
              onChange={(e) => setFormData({ ...formData, mqtt_topic: e.target.value })}
              placeholder="factory/plc/data"
              className="bg-slate-800 border-slate-700 text-white font-mono"
              required
            />
            <p className="text-xs text-slate-500 mt-1">
              ESP32 will publish sensor data to this topic
            </p>
          </div>

          {/* ESP32 Configuration Info */}
          <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
            <h4 className="text-sm font-semibold text-blue-300 mb-2">📡 ESP32 Configuration</h4>
            <div className="text-xs text-slate-300 space-y-1 font-mono">
              <p><span className="text-slate-500">Broker:</span> mqtt://mosquitto:1883</p>
              <p><span className="text-slate-500">Topic:</span> {formData.mqtt_topic}</p>
              <p><span className="text-slate-500">Data Format (JSON):</span></p>
              <pre className="text-xs bg-slate-950 p-2 rounded mt-1 overflow-x-auto">
{`{
  "machine_id": "${formData.id || 'YOUR_ID'}",
  "equipment_name": "${formData.name || 'YOUR_NAME'}",
  "vibration": 45.2,
  "temperature": 62.5,
  "humidity": 55.0,
  "timestamp": 1701234567
}`}
              </pre>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              className="border-slate-700 text-slate-300"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                  Adding...
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Equipment
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
