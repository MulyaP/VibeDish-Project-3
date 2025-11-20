"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { MapView } from "@/components/map-view"
import { MapPin, Clock, Package, Navigation, Phone, User } from "lucide-react"

// Dummy data for nearby ready orders
const dummyReadyOrders = [
  {
    id: "1",
    restaurantName: "Pizza Palace",
    restaurantAddress: "123 Main St, Raleigh, NC 27601",
    customerName: "John Doe",
    customerAddress: "456 Oak Ave, Raleigh, NC 27602",
    customerPhone: "(919) 555-0123",
    orderTotal: 24.99,
    estimatedTime: "15 min",
    latitude: 35.7796,
    longitude: -78.6382,
    items: ["Large Pepperoni Pizza", "Caesar Salad", "2x Soft Drinks"],
  },
  {
    id: "2",
    restaurantName: "Burger Haven",
    restaurantAddress: "789 Elm St, Raleigh, NC 27603",
    customerName: "Jane Smith",
    customerAddress: "321 Pine Rd, Raleigh, NC 27604",
    customerPhone: "(919) 555-0456",
    orderTotal: 18.50,
    estimatedTime: "20 min",
    latitude: 35.7846,
    longitude: -78.6432,
    items: ["Classic Burger", "French Fries", "Milkshake"],
  },
  {
    id: "3",
    restaurantName: "Sushi Express",
    restaurantAddress: "456 Maple Dr, Raleigh, NC 27605",
    customerName: "Bob Johnson",
    customerAddress: "789 Cedar Ln, Raleigh, NC 27606",
    customerPhone: "(919) 555-0789",
    orderTotal: 32.75,
    estimatedTime: "25 min",
    latitude: 35.7746,
    longitude: -78.6332,
    items: ["Salmon Roll", "Tuna Roll", "Miso Soup", "Edamame"],
  },
]

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

  // Convert orders to restaurant format for map
  const restaurantsForMap = dummyReadyOrders.map((order) => ({
    id: order.id,
    name: order.restaurantName,
    address: order.restaurantAddress,
    latitude: order.latitude,
    longitude: order.longitude,
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
              {dummyReadyOrders.length} orders available for pickup
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
                    onRestaurantSelect={(restaurant) => {
                      const order = dummyReadyOrders.find(o => o.id === restaurant.id)
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
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {dummyReadyOrders.map((order) => (
                <Card key={order.id} className="border-2 hover:border-primary/50 transition-colors">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <CardTitle className="text-lg">{order.restaurantName}</CardTitle>
                        <CardDescription className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {order.restaurantAddress}
                        </CardDescription>
                      </div>
                      <Badge variant="secondary" className="ml-2">
                        <Clock className="h-3 w-3 mr-1" />
                        {order.estimatedTime}
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

                    <div className="flex items-center justify-between pt-2 border-t">
                      <div>
                        <p className="text-xs text-muted-foreground">Total</p>
                        <p className="text-lg font-semibold">${order.orderTotal.toFixed(2)}</p>
                      </div>
                      <Button onClick={() => handleAcceptOrder(order.id)}>
                        Accept Order
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </section>

      
    </div>
  )
}