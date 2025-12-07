'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { Loader2, Info } from 'lucide-react'

interface NutritionData {
  meal_name: string
  serving_size?: string
  calories: number
  protein_g: number
  carbs_g: number
  fat_g: number
  fiber_g: number
  sugar_g: number
  sodium_mg: number
  source?: string
  source_message?: string
  food_url?: string
  food_type?: string
  error?: string
}

interface NutritionFactsProps {
  mealId: string
  mealName: string
}

export function NutritionFacts({ mealId, mealName }: NutritionFactsProps) {
  const [nutrition, setNutrition] = useState<NutritionData | null>(null)
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)

  const fetchNutrition = async () => {
    if (nutrition) return // Already loaded
    
    setLoading(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/catalog/meals/${mealId}/nutrition`)
      const data = await response.json()
      setNutrition(data)
    } catch (error) {
      setNutrition({ 
        meal_name: mealName, 
        error: 'Failed to load nutrition data',
        calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0, fiber_g: 0, sugar_g: 0, sodium_mg: 0
      })
    } finally {
      setLoading(false)
    }
  }

  const handleOpenChange = (newOpen: boolean) => {
    setOpen(newOpen)
    if (newOpen) {
      fetchNutrition()
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <Info className="h-4 w-4" />
          Nutrition Facts
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Nutrition Facts</DialogTitle>
        </DialogHeader>
        
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span className="ml-2">Loading nutrition data...</span>
          </div>
        ) : nutrition?.error ? (
          <Card>
            <CardContent className="pt-6">
              <p className="text-center text-muted-foreground">{nutrition.error}</p>
            </CardContent>
          </Card>
        ) : nutrition ? (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">{nutrition.meal_name}</CardTitle>
              {nutrition.serving_size && (
                <p className="text-sm text-muted-foreground">Per {nutrition.serving_size}</p>
              )}
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-center">
                <div className="text-2xl font-bold">{nutrition.calories}</div>
                <div className="text-sm text-muted-foreground">Calories</div>
              </div>
              
              <Separator />
              
              <div className="space-y-2">
                <NutrientRow label="Protein" value={nutrition.protein_g} unit="g" />
                <NutrientRow label="Carbohydrates" value={nutrition.carbs_g} unit="g" />
                <NutrientRow label="Fat" value={nutrition.fat_g} unit="g" />
                <NutrientRow label="Fiber" value={nutrition.fiber_g} unit="g" />
                <NutrientRow label="Sugar" value={nutrition.sugar_g} unit="g" />
                <NutrientRow label="Sodium" value={nutrition.sodium_mg} unit="mg" />
              </div>
              
              <div className="pt-2 space-y-2">
                {nutrition.source === "fatsecret_api" ? (
                  <>
                    <Badge variant="default" className="text-xs">
                      ✓ FatSecret API Data
                    </Badge>
                    {nutrition.source_message && (
                      <p className="text-xs text-muted-foreground">{nutrition.source_message}</p>
                    )}
                    {nutrition.food_url && (
                      <a 
                        href={nutrition.food_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-xs text-primary hover:underline block"
                      >
                        View detailed nutrition info →
                      </a>
                    )}
                  </>
                ) : (
                  <>
                    <Badge variant="secondary" className="text-xs">
                      ⚠ Estimated Data
                    </Badge>
                    {nutrition.source_message && (
                      <p className="text-xs text-muted-foreground">{nutrition.source_message}</p>
                    )}
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}

function NutrientRow({ label, value, unit }: { label: string; value: number; unit: string }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-sm">{label}</span>
      <span className="font-medium">{value}{unit}</span>
    </div>
  )
}