"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { MapView } from "@/components/map-view"
import { MapPin, Package, User } from "lucide-react"
import { acceptDeliveryOrder } from "@/lib/api"
import { authenticatedFetch } from "@/context/auth-context"
import { useToast } from "@/hooks/use-toast"

interface ReadyOrder {
  id: string
  user_id: string
  restaurant_id: string
  delivery_address: string | null
  delivery_fee: number | null
  tip_amount: number | null
  // total_compensation: number | null
  latitude: number | null
  longitude: number | null
  status: string
  distance_restaurant_delivery: number | null
  duration_restaurant_delivery: number | null
  restaurants: {
    name: string
    address: string
    latitude: number
    longitude: number
  }
  customer: {
    name: string
  }
  distance_to_restaurant: number
  duration_to_restaurant: number
  distance_to_restaurant_miles: number
  restaurant_reachable_by_road: boolean
  duration_to_restaurant_minutes: number
}

// Dummy data for nearby ready orders
// const dummyReadyOrders: ReadyOrder[] = [
//   {
//     id: "1af04cf1-e063-45ab-8b4b-5f88e1841bd0",
//     user_id: "b7597640-800f-4039-9932-aa0ed9e53dd3",
//     restaurant_id: "01391de7-d1df-40b5-8d1e-51f23953722e",
//     delivery_address: "456 Oak Ave, Raleigh, NC 27602",
//     delivery_fee: 3.5,
//     tip_amount: 2.0,
//     total_compensation: 5.5,
//     latitude: null,
//     longitude: null,
//     status: "ready",
//     distance_restaurant_delivery: 3.2,
//     duration_restaurant_delivery: 5,
//     restaurants: {
//       name: "Port City Java Oval",
//       address: "890 Oval Drive, Raleigh, North Carolina 27606, United States",
//       latitude: 35.771994,
//       longitude: -78.673872
//     },
//     customer: {
//       name: "Mulya Customer"
//     },
//     distance_to_restaurant: 14189.6,
//     duration_to_restaurant: 777.2,
//     distance_to_restaurant_miles: 8.817,
//     restaurant_reachable_by_road: true,
//     duration_to_restaurant_minutes: 13.0
//   },
//   {
//     id: "59461092-23cc-4414-b6d2-22100f114a65",
//     user_id: "b7597640-800f-4039-9932-aa0ed9e53dd3",
//     restaurant_id: "cbbd7601-86d9-4a04-9d7d-ad58573eeb32",
//     delivery_address: "321 Pine Rd, Raleigh, NC 27604",
//     delivery_fee: 2.8,
//     tip_amount: 1.5,
//     total_compensation: 4.3,
//     latitude: null,
//     longitude: null,
//     status: "ready",
//     distance_restaurant_delivery: 3.2,
//     duration_restaurant_delivery: 8.5,
//     restaurants: {
//       name: "Coco Bongo",
//       address: "2400 Hillsborough Street, Raleigh, North Carolina 27607, United States",
//       latitude: 35.787805,
//       longitude: -78.667075
//     },
//     customer: {
//       name: "Mulya Customer"
//     },
//     distance_to_restaurant: 9219.7,
//     duration_to_restaurant: 765.0,
//     distance_to_restaurant_miles: 5.729,
//     restaurant_reachable_by_road: true,
//     duration_to_restaurant_minutes: 12.8
//   }
// ]

export default function DriverPage() {
  const [selectedOrder, setSelectedOrder] = useState<string | null>(null)
  const [userLocation, setUserLocation] = useState<{ latitude: number; longitude: number } | null>(null)
  const [readyOrders, setReadyOrders] = useState<ReadyOrder[]>([])
  const { toast } = useToast()

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          })
        },
        () => {
          setUserLocation({ latitude: 35.7796, longitude: -78.6382 })
        },
        {
          enableHighAccuracy: true,
          timeout: 5000,
          maximumAge: 60000
        }
      )
    } else {
      setUserLocation({ latitude: 35.7796, longitude: -78.6382 })
    }
  }, [])

  useEffect(() => {
    if (userLocation) {
      const fetchReadyOrders = async () => {
        try {
          const response = await authenticatedFetch(
            `${process.env.NEXT_PUBLIC_API_URL}/deliveries/ready?latitude=${userLocation.latitude}&longitude=${userLocation.longitude}`
          )
          if (response.ok) {
            const data = await response.json()
            setReadyOrders(data)
          }
        } catch (error) {
          console.error('Error fetching ready orders:', error)
        }
      }
      fetchReadyOrders()
    }
  }, [userLocation])

  // Convert orders to restaurant format for map
  const restaurantsForMap = readyOrders.map((order) => ({
    id: order.id,
    name: order.restaurants.name,
    address: order.restaurants.address,
    latitude: order.restaurants.latitude,
    longitude: order.restaurants.longitude,
  }))

  const handleAcceptOrder = async (orderId: string) => {
    try {
      await acceptDeliveryOrder(orderId)
      setReadyOrders(prev => prev.filter(order => order.id !== orderId))
      toast({
        title: "Order Accepted",
        description: "You have successfully accepted the delivery order.",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to accept order",
        variant: "destructive",
      })
    }
  }

  return (
    <div className="container py-8 space-y-8">
      <div className="space-y-2">
        <h1 className="text-4xl font-bold tracking-tight">Nearby Ready Orders</h1>
        <p className="text-lg text-muted-foreground">
          {readyOrders.length} orders available for pickup
        </p>
      </div>

        <Tabs defaultValue="map" className="w-full">
          <TabsList>
            <TabsTrigger value="map">
              <MapPin className="h-4 w-4 mr-2" />
              Map View
            </TabsTrigger>
            <TabsTrigger value="cards">
              <Package className="h-4 w-4 mr-2" />
              Card View
            </TabsTrigger>
          </TabsList>

          <TabsContent value="map" className="mt-4">
            <Card className="border-2">
              <CardContent className="p-0">
                <div className="h-[600px] rounded-lg overflow-hidden">
                  <MapView 
                    restaurants={restaurantsForMap}
                    userLocation={userLocation}
                    onRestaurantSelect={(restaurant) => {
                      const order = readyOrders.find(o => o.id === restaurant.id)
                      if (order) {
                        setSelectedOrder(order.id)
                      }
                    }}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="cards" className="mt-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 items-start">
              {readyOrders.map((order) => {
                const totalDistance = (order.distance_to_restaurant_miles || 0) + (order.distance_restaurant_delivery || 0)
                const totalDuration = (order.duration_to_restaurant_minutes || 0) + (order.duration_restaurant_delivery || 0)
                
                return (
                  <Card key={order.id} className="border-2 hover:border-primary/50 transition-colors">
                    <CardHeader>
                      <div className="space-y-1">
                        <CardTitle className="text-lg">{order.restaurants.name}</CardTitle>
                        <CardDescription className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {order.restaurants.address}
                        </CardDescription>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-sm">
                          <User className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">{order.customer.name}</span>
                        </div>
                        {order.delivery_address && (
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <MapPin className="h-4 w-4" />
                            <span>{order.delivery_address}</span>
                          </div>
                        )}
                      </div>

                      <div className="space-y-2 pt-3 border-t">
                        <p className="text-sm font-semibold mb-2">Trip Details</p>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between items-center">
                            <span className="text-muted-foreground">Current → Restaurant:</span>
                            <span className="font-medium">{order.distance_to_restaurant_miles.toFixed(1)} mi • {order.duration_to_restaurant_minutes.toFixed(0)} min</span>
                          </div>
                          {order.distance_restaurant_delivery && order.duration_restaurant_delivery && (
                            <div className="flex justify-between items-center">
                              <span className="text-muted-foreground">Restaurant → Delivery:</span>
                              <span className="font-medium">{order.distance_restaurant_delivery.toFixed(1)} mi • {order.duration_restaurant_delivery.toFixed(0)} min</span>
                            </div>
                          )}
                          <div className="flex justify-between items-center pt-2 mt-2 border-t">
                            <span className="font-semibold">Total Distance & Time:</span>
                            <span className="font-semibold">{totalDistance.toFixed(1)} mi • {totalDuration.toFixed(0)} min</span>
                          </div>
                        </div>
                      </div>

                      <div className="space-y-2 pt-3 border-t">
                        <p className="text-sm font-semibold mb-2">Earnings</p>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between items-center">
                            <span className="text-muted-foreground">Delivery Fee:</span>
                            <span className="font-medium">${order.delivery_fee?.toFixed(2) || '0.00'}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-muted-foreground">Tip:</span>
                            <span className="font-medium">${order.tip_amount?.toFixed(2) || '0.00'}</span>
                          </div>
                          <div className="flex justify-between items-center pt-2 mt-2 border-t">
                            <span className="font-semibold">Total Compensation:</span>
                            <span className="font-bold text-lg text-primary">${(order.tip_amount || 0) + (order.delivery_fee || 0)}</span>
                          </div>
                        </div>
                      </div>

                      <div className="pt-3">
                        <Button onClick={() => handleAcceptOrder(order.id)} className="w-full">
                          Accept Order
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </TabsContent>
      </Tabs>
    </div>
  )
}