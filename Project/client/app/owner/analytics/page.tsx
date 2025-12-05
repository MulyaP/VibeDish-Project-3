'use client'

import { useState, useEffect } from 'react'
import { Star, TrendingUp, DollarSign, Package, Users, Award, Loader2 } from 'lucide-react'
import { getOwnerAnalytics } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

export default function OwnerAnalytics() {
  const [data, setData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    async function fetchAnalytics() {
      try {
        const analytics = await getOwnerAnalytics()
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
        <Loader2 className="w-8 h-8 animate-spin text-orange-500" />
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-purple-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{data.restaurant.name}</h1>
            <p className="text-gray-600 mt-1">Restaurant Analytics Dashboard</p>
          </div>

        </div>

        {/* Rating Overview Card */}
        <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-2xl p-8 text-white shadow-xl">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-orange-100 text-sm font-medium mb-2">Overall Rating</p>
              <div className="flex items-center gap-3">
                <span className="text-6xl font-bold">{data.restaurant.averageRating}</span>
                <div className="flex flex-col">
                  <div className="flex gap-1">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className={`w-6 h-6 ${i < Math.floor(data.restaurant.averageRating) ? 'fill-white' : 'fill-orange-300'}`} />
                    ))}
                  </div>
                  <p className="text-orange-100 text-sm mt-1">{data.restaurant.totalReviews} reviews</p>
                </div>
              </div>
            </div>
            <Award className="w-24 h-24 text-orange-200 opacity-50" />
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard 
            icon={<DollarSign className="w-6 h-6" />}
            label="Total Revenue"
            value={`$${data.stats.totalRevenue.toLocaleString()}`}
            color="green"
          />
          <StatCard 
            icon={<Package className="w-6 h-6" />}
            label="Total Orders"
            value={data.restaurant.totalOrders.toLocaleString()}
            color="blue"
          />
          <StatCard 
            icon={<Users className="w-6 h-6" />}
            label="Repeat Customers"
            value={`${data.stats.repeatCustomers}%`}
            color="purple"
          />
          <StatCard 
            icon={<TrendingUp className="w-6 h-6" />}
            label="Avg Order Value"
            value={`$${data.stats.avgOrderValue}`}
            color="orange"
          />
        </div>

        {/* Popular Dishes */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Most Popular Dishes</h2>
            <span className="text-sm text-gray-500">Ranked by orders</span>
          </div>
          <div className="space-y-4">
            {data.popularDishes.map((dish: any, index: number) => (
              <div key={dish.id} className="flex items-center gap-4 p-4 rounded-xl hover:bg-gray-50 transition-colors border border-gray-100">
                <div className="flex items-center justify-center w-12 h-12 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 text-white font-bold text-lg">
                  #{index + 1}
                </div>
                {dish.image && <img src={dish.image} alt={dish.name} className="w-12 h-12 rounded-lg object-cover" />}
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{dish.name}</h3>
                  <div className="flex items-center gap-4 mt-1">
                    <span className="text-sm text-gray-600">{dish.orders} orders</span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-bold text-gray-900">${Math.round(dish.revenue).toLocaleString()}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Reviews */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Recent Reviews</h2>
          <div className="space-y-4">
            {data.recentReviews.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No reviews yet</p>
            ) : (
              data.recentReviews.map((review: any) => (
              <div key={review.id} className="p-4 rounded-xl border border-gray-100 hover:border-orange-200 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-white font-semibold">
                      {review.customer.charAt(0)}
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">{review.customer}</p>
                      <p className="text-xs text-gray-500">{review.date}</p>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className={`w-4 h-4 ${i < review.rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`} />
                    ))}
                  </div>
                </div>
                <p className="text-gray-700 text-sm ml-13">{review.comment || 'No comment'}</p>
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
