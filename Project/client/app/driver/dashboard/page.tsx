'use client'

import { useState, useEffect } from 'react'
import { DollarSign, TrendingUp, Package, Award, Loader2 } from 'lucide-react'
import { getDriverAnalytics } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

export default function DriverDashboard() {
  const [data, setData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    async function fetchAnalytics() {
      try {
        const analytics = await getDriverAnalytics()
        setData(analytics)
      } catch (error) {
        toast({
          title: 'Error',
          description: 'Failed to load analytics data',
          variant: 'destructive'
        })
      } finally {
        setIsLoading(false)
      }
    }
    fetchAnalytics()
  }, [])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Driver Dashboard</h1>
          <p className="text-gray-600 mt-1">Your earnings and performance metrics</p>
        </div>

        <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-2xl p-8 text-white shadow-xl">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm font-medium mb-2">Total Earnings</p>
              <div className="flex items-center gap-3">
                <span className="text-6xl font-bold">${data.stats.totalEarnings}</span>
              </div>
              <p className="text-blue-100 text-sm mt-2">{data.stats.totalDeliveries} deliveries completed</p>
            </div>
            <Award className="w-24 h-24 text-blue-200 opacity-50" />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard 
            icon={<Package className="w-6 h-6" />}
            label="Total Deliveries"
            value={data.stats.totalDeliveries.toLocaleString()}
            color="blue"
          />
          <StatCard 
            icon={<DollarSign className="w-6 h-6" />}
            label="Avg Per Delivery"
            value={`$${data.stats.avgEarningsPerDelivery}`}
            color="green"
          />
          <StatCard 
            icon={<TrendingUp className="w-6 h-6" />}
            label="Total Tips"
            value={`$${data.stats.totalTips}`}
            color="purple"
          />
          <StatCard 
            icon={<DollarSign className="w-6 h-6" />}
            label="Delivery Fees"
            value={`$${data.stats.totalDeliveryFees}`}
            color="orange"
          />
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Earnings Last 7 Days</h2>
          <div className="space-y-3">
            {data.earningsByDay.map((day: any) => (
              <div key={day.date} className="flex items-center gap-4">
                <div className="w-12 text-sm font-medium text-gray-600">{day.day}</div>
                <div className="flex-1 bg-gray-100 rounded-full h-8 relative overflow-hidden">
                  <div 
                    className="bg-gradient-to-r from-blue-500 to-blue-600 h-full rounded-full flex items-center px-3"
                    style={{ width: `${Math.min((day.earnings / Math.max(...data.earningsByDay.map((d: any) => d.earnings))) * 100, 100)}%` }}
                  >
                    <span className="text-white text-sm font-semibold">${day.earnings}</span>
                  </div>
                </div>
                <div className="w-20 text-sm text-gray-600 text-right">{day.deliveries} orders</div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Top Restaurants</h2>
          <div className="space-y-4">
            {data.topRestaurants.map((restaurant: any, index: number) => (
              <div key={restaurant.id} className="flex items-center gap-4 p-4 rounded-xl hover:bg-gray-50 transition-colors border border-gray-100">
                <div className="flex items-center justify-center w-12 h-12 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 text-white font-bold text-lg">
                  #{index + 1}
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{restaurant.name}</h3>
                  <div className="flex items-center gap-4 mt-1">
                    <span className="text-sm text-gray-600">{restaurant.deliveries} deliveries</span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-bold text-gray-900">${restaurant.earnings}</p>
                  <p className="text-sm text-gray-500">earned</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Recent Deliveries</h2>
          <div className="space-y-4">
            {data.recentDeliveries.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No deliveries yet</p>
            ) : (
              data.recentDeliveries.map((delivery: any) => (
                <div key={delivery.id} className="p-4 rounded-xl border border-gray-100 hover:border-blue-200 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <p className="font-semibold text-gray-900">{delivery.restaurant}</p>
                      <p className="text-sm text-gray-600">Customer: {delivery.customer}</p>
                      <p className="text-xs text-gray-500">{new Date(delivery.date).toLocaleString()}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-green-600">${delivery.earnings}</p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, label, value, color }: { 
  icon: React.ReactNode
  label: string
  value: string
  color: 'green' | 'blue' | 'purple' | 'orange'
}) {
  const colorClasses = {
    green: 'from-green-500 to-green-600',
    blue: 'from-blue-500 to-blue-600',
    purple: 'from-purple-500 to-purple-600',
    orange: 'from-orange-500 to-orange-600'
  }

  return (
    <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${colorClasses[color]} flex items-center justify-center text-white mb-4`}>
        {icon}
      </div>
      <p className="text-gray-600 text-sm mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  )
}
