'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Star, Loader2, Store, Truck } from 'lucide-react'
import { submitRestaurantFeedback, submitDriverFeedback } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

interface FeedbackModalProps {
  orderId: string
  restaurantName: string
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
  hasRestaurantFeedback?: boolean
  hasDriverFeedback?: boolean
}

export function FeedbackModal({ orderId, restaurantName, open, onOpenChange, onSuccess, hasRestaurantFeedback, hasDriverFeedback }: FeedbackModalProps) {
  const [restaurantRating, setRestaurantRating] = useState(0)
  const [restaurantHoveredRating, setRestaurantHoveredRating] = useState(0)
  const [restaurantComment, setRestaurantComment] = useState('')
  const [driverRating, setDriverRating] = useState(0)
  const [driverHoveredRating, setDriverHoveredRating] = useState(0)
  const [driverComment, setDriverComment] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()

  const handleRestaurantSubmit = async () => {
    if (restaurantRating === 0) {
      toast({
        title: 'Rating required',
        description: 'Please select a rating before submitting',
        variant: 'destructive',
      })
      return
    }

    setIsSubmitting(true)
    try {
      await submitRestaurantFeedback(orderId, restaurantRating, restaurantComment)
      toast({
        title: 'Restaurant feedback submitted',
        description: 'Thank you for your feedback!',
      })
      setRestaurantRating(0)
      setRestaurantComment('')
      onSuccess?.()
    } catch (err) {
      toast({
        title: 'Error',
        description: err instanceof Error ? err.message : 'Failed to submit feedback',
        variant: 'destructive',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDriverSubmit = async () => {
    if (driverRating === 0) {
      toast({
        title: 'Rating required',
        description: 'Please select a rating before submitting',
        variant: 'destructive',
      })
      return
    }

    setIsSubmitting(true)
    try {
      await submitDriverFeedback(orderId, driverRating, driverComment)
      toast({
        title: 'Driver feedback submitted',
        description: 'Thank you for your feedback!',
      })
      setDriverRating(0)
      setDriverComment('')
      onSuccess?.()
    } catch (err) {
      toast({
        title: 'Error',
        description: err instanceof Error ? err.message : 'Failed to submit feedback',
        variant: 'destructive',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    onOpenChange(false)
    setRestaurantRating(0)
    setRestaurantComment('')
    setDriverRating(0)
    setDriverComment('')
  }

  const StarRating = ({ rating, hoveredRating, onRate, onHover }: any) => (
    <div className="flex gap-2">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          onClick={() => onRate(star)}
          onMouseEnter={() => onHover(star)}
          onMouseLeave={() => onHover(0)}
          className="transition-transform hover:scale-110"
        >
          <Star
            className={`h-8 w-8 ${
              star <= (hoveredRating || rating)
                ? 'fill-yellow-400 text-yellow-400'
                : 'text-gray-300'
            }`}
          />
        </button>
      ))}
    </div>
  )

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Rate Your Order</DialogTitle>
          <DialogDescription>
            Share your experience with the restaurant and delivery
          </DialogDescription>
        </DialogHeader>
        
        <Tabs defaultValue="restaurant" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="restaurant" disabled={hasRestaurantFeedback}>
              <Store className="h-4 w-4 mr-2" />
              Restaurant
            </TabsTrigger>
            <TabsTrigger value="driver" disabled={hasDriverFeedback}>
              <Truck className="h-4 w-4 mr-2" />
              Driver
            </TabsTrigger>
          </TabsList>

          <TabsContent value="restaurant" className="space-y-4 py-4">
            {hasRestaurantFeedback ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                You've already submitted restaurant feedback
              </p>
            ) : (
              <>
                <div className="space-y-2">
                  <Label>Rate {restaurantName}</Label>
                  <StarRating
                    rating={restaurantRating}
                    hoveredRating={restaurantHoveredRating}
                    onRate={setRestaurantRating}
                    onHover={setRestaurantHoveredRating}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="restaurant-comment">Comments (Optional)</Label>
                  <Textarea
                    id="restaurant-comment"
                    placeholder="How was the food quality and service?"
                    value={restaurantComment}
                    onChange={(e) => setRestaurantComment(e.target.value)}
                    rows={4}
                  />
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={handleClose} disabled={isSubmitting}>
                    Cancel
                  </Button>
                  <Button onClick={handleRestaurantSubmit} disabled={isSubmitting}>
                    {isSubmitting ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      'Submit'
                    )}
                  </Button>
                </DialogFooter>
              </>
            )}
          </TabsContent>

          <TabsContent value="driver" className="space-y-4 py-4">
            {hasDriverFeedback ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                You've already submitted driver feedback
              </p>
            ) : (
              <>
                <div className="space-y-2">
                  <Label>Rate Delivery Driver</Label>
                  <StarRating
                    rating={driverRating}
                    hoveredRating={driverHoveredRating}
                    onRate={setDriverRating}
                    onHover={setDriverHoveredRating}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="driver-comment">Comments (Optional)</Label>
                  <Textarea
                    id="driver-comment"
                    placeholder="How was the delivery experience?"
                    value={driverComment}
                    onChange={(e) => setDriverComment(e.target.value)}
                    rows={4}
                  />
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={handleClose} disabled={isSubmitting}>
                    Cancel
                  </Button>
                  <Button onClick={handleDriverSubmit} disabled={isSubmitting}>
                    {isSubmitting ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      'Submit'
                    )}
                  </Button>
                </DialogFooter>
              </>
            )}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
