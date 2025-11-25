"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { MapView } from "@/components/map-view"
import { MapPin, Clock, Package, Navigation, Phone, User } from "lucide-react"

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

// Dummy data for active orders
const dummyActiveOrders = [
  {
    id: "active-1",
    restaurantName: "Thai Garden",
    customerName: "Alice Williams",
    customerAddress: "111 Cherry St, Raleigh, NC 27607",
    customerPhone: "(919) 555-0321",
    orderTotal: 28.50,
    status: "picked_up",
    pickedUpAt: "2:30 PM",
    estimatedDelivery: "2:50 PM",
    items: ["Pad Thai", "Spring Rolls", "Thai Iced Tea"],
  },
]

export default function DriverPage() {
  const [selectedOrder, setSelectedOrder] = useState<string | null>(null)
  const [userLocation, setUserLocation] = useState<{ latitude: number; longitude: number } | null>(null)
  const [readyOrders, setReadyOrders] = useState<ReadyOrder[]>([])

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          })
        },
        (error) => {
          console.error('Error getting location:', error)
          setUserLocation({ latitude: 35.7796, longitude: -78.6382 })
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
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
          const response = await fetch(
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

  const handleAcceptOrder = (orderId: string) => {
    // TODO: Implement order acceptance logic
    console.log("Accepting order:", orderId)
  }

  return (
    <div className="container py-8 space-y-8">
      {/* Page Header */}
      <div className="space-y-2">
        <h1 className="text-4xl font-bold tracking-tight">Delivery Driver Dashboard</h1>
        <p className="text-lg text-muted-foreground">
          View nearby ready orders and manage your active deliveries
        </p>
      </div>

      {/* Active Orders Section */}
      <section className="space-y-4">
        <div>
          <h2 className="text-2xl font-semibold">Active Orders</h2>
          <p className="text-sm text-muted-foreground">
            Orders you are currently delivering
          </p>
        </div>

        {dummyActiveOrders.length === 0 ? (
          <Card className="border-2 border-dashed">
            <CardContent className="py-12 text-center">
              <Package className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-lg font-medium mb-2">No Active Orders</p>
              <p className="text-sm text-muted-foreground">
                Accept an order from the nearby ready orders section to get started
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {dummyActiveOrders.map((order) => (
              <Card key={order.id} className="border-2 border-primary/50">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="text-lg">{order.restaurantName}</CardTitle>
                      <CardDescription>Order #{order.id}</CardDescription>
                    </div>
                    <Badge variant="default" className="ml-2">
                      {order.status === "picked_up" ? "In Transit" : "Picking Up"}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <User className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{order.customerName}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <MapPin className="h-4 w-4" />
                      <span>{order.customerAddress}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Phone className="h-4 w-4" />
                      <span>{order.customerPhone}</span>
                    </div>
                  </div>

                  <div className="space-y-1">
                    <p className="text-sm font-medium">Order Items:</p>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      {order.items.map((item, idx) => (
                        <li key={idx} className="flex items-center gap-2">
                          <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="space-y-2 pt-2 border-t">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Picked Up:</span>
                      <span className="font-medium">{order.pickedUpAt}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Est. Delivery:</span>
                      <span className="font-medium">{order.estimatedDelivery}</span>
                    </div>
                    <div className="flex items-center justify-between pt-2 border-t">
                      <div>
                        <p className="text-xs text-muted-foreground">Total</p>
                        <p className="text-lg font-semibold">${order.orderTotal.toFixed(2)}</p>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm">
                          <Navigation className="h-4 w-4 mr-2" />
                          Navigate
                        </Button>
                        <Button size="sm">
                          Mark Delivered
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* Nearby Ready Orders Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold">Nearby Ready Orders</h2>
            <p className="text-sm text-muted-foreground">
              {readyOrders.length} orders available for pickup
            </p>
          </div>
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
      </section>

      
    </div>
  )
}