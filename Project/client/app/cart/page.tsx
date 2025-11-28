"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ShoppingCart, Trash2, Loader2, Plus, Minus, AlertCircle, CheckCircle2, MapPin } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { geocodeAddress } from "@/lib/geocoding"
import { useAuth } from "@/context/auth-context"
import { getCart, updateCartItem, removeFromCart, clearCart, checkoutCart } from "@/lib/api"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"

interface CartItem {
  item_id: string
  meal_id: string
  meal_name: string
  restaurant_id: string
  qty: number
  unit_price: number
  line_total: number
  surplus_left: number
}

interface Cart {
  cart_id: string
  items: CartItem[]
  cart_total: number
}

export default function CartPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading: authLoading } = useAuth()
  const [cart, setCart] = useState<Cart | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [updatingItems, setUpdatingItems] = useState<Set<string>>(new Set())
  const [checkingOut, setCheckingOut] = useState(false)
  const [checkoutSuccess, setCheckoutSuccess] = useState(false)
  const [deliveryAddress, setDeliveryAddress] = useState("")
  const [latitude, setLatitude] = useState<number | null>(null)
  const [longitude, setLongitude] = useState<number | null>(null)
  const [formattedAddress, setFormattedAddress] = useState("")
  const [isGeocodingLoading, setIsGeocodingLoading] = useState(false)
  const [tipAmount, setTipAmount] = useState(0)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    } else if (isAuthenticated) {
      loadCart()
    }
  }, [isAuthenticated, authLoading, router])

  const loadCart = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getCart()
      setCart(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load cart")
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateQuantity = async (itemId: string, newQty: number) => {
    if (newQty < 1) return

    setUpdatingItems(prev => new Set(prev).add(itemId))
    try {
      const data = await updateCartItem(itemId, newQty)
      setCart(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update quantity")
    } finally {
      setUpdatingItems(prev => {
        const next = new Set(prev)
        next.delete(itemId)
        return next
      })
    }
  }

  const handleRemoveItem = async (itemId: string) => {
    setUpdatingItems(prev => new Set(prev).add(itemId))
    try {
      const data = await removeFromCart(itemId)
      setCart(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove item")
    } finally {
      setUpdatingItems(prev => {
        const next = new Set(prev)
        next.delete(itemId)
        return next
      })
    }
  }

  const handleClearCart = async () => {
    setLoading(true)
    try {
      const data = await clearCart()
      setCart(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to clear cart")
    } finally {
      setLoading(false)
    }
  }

  const handleGeocodeAddress = async () => {
    if (!deliveryAddress || deliveryAddress.trim().length === 0) {
      setError("Please enter a delivery address")
      return
    }

    setIsGeocodingLoading(true)
    setError(null)
    try {
      const result = await geocodeAddress(deliveryAddress)
      setLatitude(result.latitude)
      setLongitude(result.longitude)
      setFormattedAddress(result.place_name)
    } catch (error) {
      setError(error instanceof Error ? error.message : "Failed to locate address")
    } finally {
      setIsGeocodingLoading(false)
    }
  }

  const handleCheckout = async () => {
    if (latitude === null || longitude === null) {
      setError("Please locate your delivery address first")
      return
    }

    setCheckingOut(true)
    setError(null)
    try {
      let checkoutBody = {
        deliveryAddress: deliveryAddress,
        latitude: latitude,
        longitude: longitude,
        tipAmount: tipAmount,
        total : total,
        tax: tax,
        deliveryFee: deliveryFee
      }
      const result = await checkoutCart(checkoutBody)
      setCheckoutSuccess(true)
      // Reload cart after successful checkout
      setTimeout(() => {
        router.push(`/orders`)
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to checkout")
      setCheckingOut(false)
    }
  }

  if (authLoading || loading) {
    return (
      <div className="container py-12 flex justify-center items-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (checkoutSuccess) {
    return (
      <div className="container py-12">
        <Card className="max-w-md mx-auto">
          <CardContent className="pt-6 text-center space-y-4">
            <CheckCircle2 className="h-16 w-16 text-green-500 mx-auto" />
            <h2 className="text-2xl font-bold">Order Placed Successfully!</h2>
            <p className="text-muted-foreground">Redirecting to orders page...</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const isEmpty = !cart || cart.items.length === 0

  // Calculate fees
  const subtotal = cart?.cart_total || 0
  const deliveryFee = Math.max(4.00, subtotal * 0.10)
  const tax = subtotal * 0.02
  const total = subtotal + deliveryFee + tax + tipAmount

  return (
    <div className="container py-12">
      {/* Header */}
      <div className="space-y-4 mb-8">
        <div className="flex items-center gap-3">
          <ShoppingCart className="h-8 w-8 text-primary" />
          <h1 className="text-4xl font-bold tracking-tight">Shopping Cart</h1>
        </div>
        <p className="text-lg text-muted-foreground">
          Review your items and proceed to checkout
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-lg mb-6 flex items-start gap-2">
          <AlertCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <p className="font-medium">{error}</p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setError(null)}
          >
            Dismiss
          </Button>
        </div>
      )}

      {isEmpty ? (
        <Card>
          <CardContent className="pt-12 pb-12 text-center space-y-4">
            <ShoppingCart className="h-16 w-16 mx-auto text-muted-foreground" />
            <div className="space-y-2">
              <h2 className="text-2xl font-bold">Your cart is empty</h2>
              <p className="text-muted-foreground">
                Browse our deals and add some delicious meals!
              </p>
            </div>
            <Button onClick={() => router.push('/browse')} size="lg">
              Browse Meals
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Cart Items */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {cart.items.length} {cart.items.length === 1 ? 'item' : 'items'} in your cart
              </p>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive">
                    <Trash2 className="h-4 w-4 mr-2" />
                    Clear Cart
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Clear your cart?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This will remove all items from your cart. This action cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={handleClearCart}>
                      Clear Cart
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>

            {cart.items.map((item) => {
              const isUpdating = updatingItems.has(item.item_id)
              
              return (
                <Card key={item.item_id}>
                  <CardContent className="pt-6">
                    <div className="flex gap-4">
                      <div className="flex-1 space-y-3">
                        <div>
                          <h3 className="font-semibold text-lg">{item.meal_name}</h3>
                          <p className="text-sm text-muted-foreground">
                            {item.surplus_left > 0 && (
                              <Badge variant="secondary" className="mt-1">
                                {item.surplus_left} available
                              </Badge>
                            )}
                          </p>
                        </div>

                        <div className="flex items-center gap-3">
                          <div className="flex items-center border rounded-lg">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => handleUpdateQuantity(item.item_id, item.qty - 1)}
                              disabled={isUpdating || item.qty <= 1}
                            >
                              <Minus className="h-4 w-4" />
                            </Button>
                            <span className="px-4 font-medium">{item.qty}</span>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => handleUpdateQuantity(item.item_id, item.qty + 1)}
                              disabled={isUpdating || item.qty >= item.surplus_left}
                            >
                              <Plus className="h-4 w-4" />
                            </Button>
                          </div>

                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-destructive hover:text-destructive"
                                disabled={isUpdating}
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Remove
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Remove item?</AlertDialogTitle>
                                <AlertDialogDescription>
                                  Remove {item.meal_name} from your cart?
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction onClick={() => handleRemoveItem(item.item_id)}>
                                  Remove
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </div>
                      </div>

                      <div className="text-right space-y-1">
                        <p className="text-sm text-muted-foreground">
                          ${item.unit_price.toFixed(2)} each
                        </p>
                        <p className="text-xl font-bold">
                          ${item.line_total.toFixed(2)}
                        </p>
                      </div>
                    </div>

                    {isUpdating && (
                      <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Updating...
                      </div>
                    )}
                  </CardContent>
                </Card>
              )
            })}
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <Card className="sticky top-20">
              <CardHeader>
                <CardTitle>Order Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Subtotal</span>
                    <span>${subtotal.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Delivery Fee</span>
                    <span>${deliveryFee.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Tax (2%)</span>
                    <span>${tax.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Tip</span>
                    <span>${tipAmount.toFixed(2)}</span>
                  </div>
                </div>

                <Separator />

                <div className="flex justify-between text-lg font-bold">
                  <span>Total</span>
                  <span>${total.toFixed(2)}</span>
                </div>

                <Separator />

                <div className="space-y-2">
                  <Label htmlFor="tip-amount">Tip Amount</Label>
                  <Input
                    id="tip-amount"
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="0.00"
                    value={tipAmount || ''}
                    onChange={(e) => setTipAmount(parseFloat(e.target.value) || 0)}
                  />
                </div>

                <Separator />

                <div className="space-y-3">
                  <div className="space-y-2">
                    <Label htmlFor="delivery-address">Delivery Address</Label>
                    <Input
                      id="delivery-address"
                      type="text"
                      placeholder="123 Main St, City, State, ZIP"
                      value={deliveryAddress}
                      onChange={(e) => {
                        setDeliveryAddress(e.target.value)
                        setLatitude(null)
                        setLongitude(null)
                        setFormattedAddress("")
                      }}
                    />
                  </div>

                  <Button
                    type="button"
                    variant="outline"
                    className="w-full gap-2"
                    onClick={handleGeocodeAddress}
                    disabled={isGeocodingLoading || !deliveryAddress}
                  >
                    {isGeocodingLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Locating Address...
                      </>
                    ) : (
                      <>
                        <MapPin className="h-4 w-4" />
                        Locate Address
                      </>
                    )}
                  </Button>

                  {latitude !== null && longitude !== null && (
                    <div className="rounded-lg bg-muted p-3 space-y-1">
                      <p className="text-xs font-medium text-muted-foreground">Location Found</p>
                      {formattedAddress && (
                        <p className="text-sm font-medium">{formattedAddress}</p>
                      )}
                    </div>
                  )}
                </div>

                <Button
                  className="w-full"
                  size="lg"
                  onClick={handleCheckout}
                  disabled={checkingOut || isEmpty || latitude === null || longitude === null}
                >
                  {checkingOut ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    'Proceed to Checkout'
                  )}
                </Button>

                <p className="text-xs text-muted-foreground text-center">
                  Items are reserved at checkout. Prices may change before then.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  )
}

