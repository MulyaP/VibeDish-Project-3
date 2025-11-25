"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Package, Loader2 } from "lucide-react"
import { format } from "date-fns"
import { Button } from "@/components/ui/button"
import { getOwnerOrders, updateOrderStatus } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

interface Order {
  id: string
  customer_name: string
  customer_address: string
  order_placement_time: string
  items: { name: string; qty: number }[]
  total: number
  status: string
}

const STATUS_CONFIG = {
  pending: { label: "Pending", variant: "secondary" as const },
  accepted: { label: "accepted", variant: "default" as const },
  ready: { label: "Ready", variant: "default" as const },
  completed: { label: "Completed", variant: "default" as const },
  cancelled: { label: "Cancelled", variant: "destructive" as const }
}

export default function OwnerOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    loadOrders()
  }, [])

  const loadOrders = async () => {
    try {
      setLoading(true)
      const data = await getOwnerOrders()
      setOrders(data)
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to load orders",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), "MMM dd, yyyy 'at' hh:mm a")
    } catch {
      return dateString
    }
  }

  const getItemsSummary = (items: { name: string; qty: number }[]) => {
    return items.map(item => `${item.name} (x${item.qty})`).join(", ")
  }

  const pendingOrders = orders.filter(order => order.status === "pending")
  const acceptedOrders = orders.filter(order => order.status === "accepted")
  const readyOrders = orders.filter(order => order.status === "ready")

  const handleAccept = async (orderId: string) => {
    try {
      await updateOrderStatus(orderId, "accepted")
      toast({
        title: "Success",
        description: "Order accepted"
      })
      loadOrders()
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to accept order",
        variant: "destructive"
      })
    }
  }

  const handleReject = async (orderId: string) => {
    try {
      await updateOrderStatus(orderId, "rejected")
      toast({
        title: "Success",
        description: "Order rejected"
      })
      loadOrders()
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to reject order",
        variant: "destructive"
      })
    }
  }

  const handleMarkReady = async (orderId: string) => {
    try {
      await updateOrderStatus(orderId, "ready")
      toast({
        title: "Success",
        description: "Order marked as ready"
      })
      loadOrders()
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to mark order as ready",
        variant: "destructive"
      })
    }
  }

  const renderPendingOrderTable = (orderList: Order[]) => (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Customer Name</TableHead>
          <TableHead>Customer Address</TableHead>
          <TableHead>Order Placement Time</TableHead>
          <TableHead>Items Summary</TableHead>
          <TableHead>Total</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {orderList.map((order) => (
          <TableRow key={order.id} className="h-16">
            <TableCell className="font-medium py-4">{order.customer_name}</TableCell>
            <TableCell className="py-4">{order.customer_address}</TableCell>
            <TableCell className="py-4">{formatDate(order.order_placement_time)}</TableCell>
            <TableCell className="max-w-xs truncate py-4">{getItemsSummary(order.items)}</TableCell>
            <TableCell className="font-semibold py-4">${order.total.toFixed(2)}</TableCell>
            <TableCell className="py-4">
              <div className="flex gap-2">
                <Button size="sm" onClick={() => handleAccept(order.id)}>Accept</Button>
                <Button size="sm" variant="destructive" onClick={() => handleReject(order.id)}>Reject</Button>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )

  const renderAcceptedOrderTable = (orderList: Order[]) => (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Customer Name</TableHead>
          <TableHead>Customer Address</TableHead>
          <TableHead>Order Placement Time</TableHead>
          <TableHead>Items Summary</TableHead>
          <TableHead>Total</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {orderList.map((order) => (
          <TableRow key={order.id} className="h-16">
            <TableCell className="font-medium py-4">{order.customer_name}</TableCell>
            <TableCell className="py-4">{order.customer_address}</TableCell>
            <TableCell className="py-4">{formatDate(order.order_placement_time)}</TableCell>
            <TableCell className="max-w-xs truncate py-4">{getItemsSummary(order.items)}</TableCell>
            <TableCell className="font-semibold py-4">${order.total.toFixed(2)}</TableCell>
            <TableCell className="py-4">
              <Button size="sm" onClick={() => handleMarkReady(order.id)}>Mark Ready</Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )

  const renderReadyOrderTable = (orderList: Order[]) => (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Customer Name</TableHead>
          <TableHead>Customer Address</TableHead>
          <TableHead>Order Placement Time</TableHead>
          <TableHead>Items Summary</TableHead>
          <TableHead>Total</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {orderList.map((order) => (
          <TableRow key={order.id} className="h-16">
            <TableCell className="font-medium py-4">{order.customer_name}</TableCell>
            <TableCell className="py-4">{order.customer_address}</TableCell>
            <TableCell className="py-4">{formatDate(order.order_placement_time)}</TableCell>
            <TableCell className="max-w-xs truncate py-4">{getItemsSummary(order.items)}</TableCell>
            <TableCell className="font-semibold py-4">${order.total.toFixed(2)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )

  if (loading) {
    return (
      <div className="container py-12 flex justify-center items-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="container py-12">
      <div className="space-y-4 mb-8">
        <div className="flex items-center gap-3">
          <Package className="h-8 w-8 text-primary" />
          <h1 className="text-4xl font-bold tracking-tight">Restaurant Orders</h1>
        </div>
        <p className="text-lg text-muted-foreground">
          Manage and track all incoming orders
        </p>
      </div>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Pending Orders ({pendingOrders.length})</CardTitle>
          </CardHeader>
          <CardContent>
            {pendingOrders.length > 0 ? renderPendingOrderTable(pendingOrders) : (
              <p className="text-muted-foreground text-center py-8">No pending orders</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Accepted Orders ({acceptedOrders.length})</CardTitle>
          </CardHeader>
          <CardContent>
            {acceptedOrders.length > 0 ? renderAcceptedOrderTable(acceptedOrders) : (
              <p className="text-muted-foreground text-center py-8">No accepted orders</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Ready Orders ({readyOrders.length})</CardTitle>
          </CardHeader>
          <CardContent>
            {readyOrders.length > 0 ? renderReadyOrderTable(readyOrders) : (
              <p className="text-muted-foreground text-center py-8">No ready orders</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
