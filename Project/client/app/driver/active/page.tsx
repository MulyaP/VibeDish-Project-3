"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { MapPin, Package, User, Loader2 } from "lucide-react"
import { authenticatedFetch } from "@/context/auth-context"
import { updateOrderStatus } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"
import dynamic from "next/dynamic"
import { Input } from "@/components/ui/input"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

const RouteMap = dynamic(() => import("@/components/route-map").then(mod => mod.RouteMap), { ssr: false })

interface ActiveOrder {
  id: string
  restaurant_id: string
  user_id: string
  delivery_address: string
  delivery_fee: number
  tip_amount: number
  total: number
  status: string
  created_at: string
  latitude: number | null
  longitude: number | null
  restaurants: {
    name: string
    address: string
    latitude: number
    longitude: number
  }
  customer: {
    name: string
  }
}

export default function ActiveOrdersPage() {
  const [activeOrders, setActiveOrders] = useState<ActiveOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [userLocation, setUserLocation] = useState<{ latitude: number; longitude: number } | null>(null)
  const [updatingOrders, setUpdatingOrders] = useState<Set<string>>(new Set())
  const [deliveryCodeModal, setDeliveryCodeModal] = useState<{ open: boolean; orderId: string } | null>(null)
  const [inputCode, setInputCode] = useState("")
  const { toast } = useToast()

  useEffect(() => {
    fetchActiveOrders()
    
    if (navigator.geolocation) {
      const watchId = navigator.geolocation.watchPosition(
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
        { enableHighAccuracy: true, maximumAge: 0 }
      )
      
      return () => navigator.geolocation.clearWatch(watchId)
    } else {
      setUserLocation({ latitude: 35.7796, longitude: -78.6382 })
    }
  }, [])

  const fetchActiveOrders = async () => {
    try {
      const response = await authenticatedFetch(
        `${process.env.NEXT_PUBLIC_API_URL}/deliveries/active`
      )
      if (response.ok) {
        const data = await response.json()
        setActiveOrders(data)
      }
    } catch (error) {
      console.error('Error fetching active orders:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStatusUpdate = async (orderId: string, currentStatus: string) => {
    if (currentStatus === "out-for-delivery") {
      setDeliveryCodeModal({ open: true, orderId })
      setInputCode("")
      return
    }
    
    setUpdatingOrders(prev => new Set(prev).add(orderId))
    try {
      await updateOrderStatus(orderId, "out-for-delivery")
      
      toast({
        title: "Status Updated",
        description: "Order marked as picked up"
      })
      
      await fetchActiveOrders()
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update status",
        variant: "destructive"
      })
    } finally {
      setUpdatingOrders(prev => {
        const next = new Set(prev)
        next.delete(orderId)
        return next
      })
    }
  }

  const handleDeliveryCodeSubmit = async () => {
    if (!deliveryCodeModal) return
    
    setUpdatingOrders(prev => new Set(prev).add(deliveryCodeModal.orderId))
    try {
      await updateOrderStatus(deliveryCodeModal.orderId, "delivered", inputCode)
      
      toast({
        title: "Status Updated",
        description: "Order marked as delivered"
      })
      
      setDeliveryCodeModal(null)
      setInputCode("")
      await fetchActiveOrders()
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update status",
        variant: "destructive"
      })
    } finally {
      setUpdatingOrders(prev => {
        const next = new Set(prev)
        next.delete(deliveryCodeModal.orderId)
        return next
      })
    }
  }

  if (loading) {
    return (
      <div className="container py-8 flex justify-center items-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="container py-8 space-y-8">
      <div className="space-y-2">
        <h1 className="text-4xl font-bold tracking-tight">Active Orders</h1>
        <p className="text-lg text-muted-foreground">
          Orders you are currently delivering
        </p>
      </div>

      {activeOrders.length === 0 ? (
        <Card className="border-2 border-dashed">
          <CardContent className="py-12 text-center">
            <Package className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium mb-2">No Active Orders</p>
            <p className="text-sm text-muted-foreground">
              Accept an order from the nearby orders page to get started
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {activeOrders.map((order) => (
            <Card key={order.id} className="border-2 border-primary/50">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-lg">{order.restaurants.name}</CardTitle>
                    <CardDescription>Order #{order.id.slice(0, 8)}</CardDescription>
                  </div>
                  <Badge variant="default" className="ml-2">
                    {order.status === "out-for-delivery" ? "In Transit" : "Assigned"}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{order.customer.name}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <MapPin className="h-4 w-4" />
                    <span>{order.delivery_address}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <MapPin className="h-4 w-4" />
                    <span className="text-xs">Restaurant: {order.restaurants.address}</span>
                  </div>
                </div>

                <div className="space-y-2 pt-2 border-t">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Delivery Fee:</span>
                    <span className="font-medium">${order.delivery_fee.toFixed(2)}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Tip:</span>
                    <span className="font-medium">${order.tip_amount.toFixed(2)}</span>
                  </div>
                  <div className="flex items-center justify-between pt-2 border-t">
                    <div>
                      <p className="text-xs text-muted-foreground">Total Earnings</p>
                      <p className="text-lg font-semibold">${(order.delivery_fee + order.tip_amount).toFixed(2)}</p>
                    </div>
                    <Button 
                      size="sm"
                      onClick={() => handleStatusUpdate(order.id, order.status)}
                      disabled={updatingOrders.has(order.id)}
                    >
                      {updatingOrders.has(order.id) ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        order.status === "assigned" ? "Mark Picked Up" : "Mark Delivered"
                      )}
                    </Button>
                  </div>
                </div>

                {userLocation && (() => {
                  const destination = order.status === "out-for-delivery" && order.latitude && order.longitude
                    ? { latitude: order.latitude, longitude: order.longitude }
                    : { latitude: order.restaurants.latitude, longitude: order.restaurants.longitude }
                  
                  return (
                    <div className="pt-4 border-t">
                      <h4 className="text-sm font-semibold mb-3">Live Tracking</h4>
                      <div className="h-[300px] rounded-lg overflow-hidden border">
                        <RouteMap
                          origin={userLocation}
                          destination={destination}
                        />
                      </div>
                    </div>
                  )
                })()}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={deliveryCodeModal?.open || false} onOpenChange={(open) => !open && setDeliveryCodeModal(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Enter Delivery Code</DialogTitle>
            <DialogDescription>
              Please enter the 6-digit delivery code to confirm delivery
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Input
              type="text"
              placeholder="Enter 6-digit code"
              value={inputCode}
              onChange={(e) => setInputCode(e.target.value)}
              maxLength={6}
              className="text-center text-lg font-mono"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeliveryCodeModal(null)}>
              Cancel
            </Button>
            <Button 
              onClick={handleDeliveryCodeSubmit}
              disabled={inputCode.length !== 6 || updatingOrders.has(deliveryCodeModal?.orderId || "")}
            >
              {updatingOrders.has(deliveryCodeModal?.orderId || "") ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Confirm Delivery"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
