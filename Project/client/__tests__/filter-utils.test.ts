// Utility function tests for meal filtering logic

interface Meal {
  id: string
  name: string
  tags: string[]
  allergens: string[]
}

interface Filters {
  vegetarian: boolean
  vegan: boolean
  gluten_free: boolean
  exclude_allergens: string
}

// Extract the filtering logic into a testable utility function
export const filterMeals = (meals: Meal[], filters: Filters, searchQuery = '') => {
  return meals.filter((meal) => {
    const matchesSearch = meal.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      meal.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    
    const matchesVegetarian = !filters.vegetarian || meal.tags.some(tag => tag.toLowerCase().includes('vegetarian'))
    const matchesVegan = !filters.vegan || meal.tags.some(tag => tag.toLowerCase().includes('vegan'))
    const matchesGlutenFree = !filters.gluten_free || meal.tags.some(tag => tag.toLowerCase().includes('gluten') && tag.toLowerCase().includes('free'))
    
    const matchesAllergens = !filters.exclude_allergens || 
      !meal.allergens.some(allergen => 
        filters.exclude_allergens.toLowerCase().split(',').some(excluded => 
          allergen.toLowerCase().includes(excluded.trim())
        )
      )
    
    return matchesSearch && matchesVegetarian && matchesVegan && matchesGlutenFree && matchesAllergens
  })
}

describe('Filter Utils', () => {
  const mockMeals: Meal[] = [
    {
      id: '1',
      name: 'Veggie Burger',
      tags: ['vegetarian', 'healthy'],
      allergens: ['gluten']
    },
    {
      id: '2',
      name: 'Vegan Salad',
      tags: ['vegan', 'gluten free'],
      allergens: []
    },
    {
      id: '3',
      name: 'Chicken Sandwich',
      tags: ['protein'],
      allergens: ['gluten', 'dairy']
    }
  ]

  describe('filterMeals', () => {
    test('returns all meals when no filters applied', () => {
      const filters = { vegetarian: false, vegan: false, gluten_free: false, exclude_allergens: '' }
      const result = filterMeals(mockMeals, filters)
      expect(result).toHaveLength(3)
    })

    test('filters vegetarian meals correctly', () => {
      const filters = { vegetarian: true, vegan: false, gluten_free: false, exclude_allergens: '' }
      const result = filterMeals(mockMeals, filters)
      expect(result).toHaveLength(1)
      expect(result[0].name).toBe('Veggie Burger')
    })

    test('filters vegan meals correctly', () => {
      const filters = { vegetarian: false, vegan: true, gluten_free: false, exclude_allergens: '' }
      const result = filterMeals(mockMeals, filters)
      expect(result).toHaveLength(1)
      expect(result[0].name).toBe('Vegan Salad')
    })

    test('filters gluten free meals correctly', () => {
      const filters = { vegetarian: false, vegan: false, gluten_free: true, exclude_allergens: '' }
      const result = filterMeals(mockMeals, filters)
      expect(result).toHaveLength(1)
      expect(result[0].name).toBe('Vegan Salad')
    })

    test('excludes allergens correctly', () => {
      const filters = { vegetarian: false, vegan: false, gluten_free: false, exclude_allergens: 'gluten' }
      const result = filterMeals(mockMeals, filters)
      expect(result).toHaveLength(1)
      expect(result[0].name).toBe('Vegan Salad')
    })

    test('handles multiple allergen exclusions', () => {
      const filters = { vegetarian: false, vegan: false, gluten_free: false, exclude_allergens: 'gluten, dairy' }
      const result = filterMeals(mockMeals, filters)
      expect(result).toHaveLength(1)
      expect(result[0].name).toBe('Vegan Salad')
    })

    test('combines multiple filters with AND logic', () => {
      const filters = { vegetarian: true, vegan: false, gluten_free: false, exclude_allergens: 'dairy' }
      const result = filterMeals(mockMeals, filters)
      expect(result).toHaveLength(1)
      expect(result[0].name).toBe('Veggie Burger')
    })

    test('search query filters by name', () => {
      const filters = { vegetarian: false, vegan: false, gluten_free: false, exclude_allergens: '' }
      const result = filterMeals(mockMeals, filters, 'burger')
      expect(result).toHaveLength(1)
      expect(result[0].name).toBe('Veggie Burger')
    })

    test('search query filters by tags', () => {
      const filters = { vegetarian: false, vegan: false, gluten_free: false, exclude_allergens: '' }
      const result = filterMeals(mockMeals, filters, 'protein')
      expect(result).toHaveLength(1)
      expect(result[0].name).toBe('Chicken Sandwich')
    })

    test('case insensitive filtering', () => {
      const filters = { vegetarian: false, vegan: false, gluten_free: false, exclude_allergens: 'GLUTEN' }
      const result = filterMeals(mockMeals, filters)
      expect(result).toHaveLength(1)
      expect(result[0].name).toBe('Vegan Salad')
    })

    test('returns empty array when no matches', () => {
      const filters = { vegetarian: true, vegan: false, gluten_free: false, exclude_allergens: 'gluten' }
      const result = filterMeals(mockMeals, filters)
      expect(result).toHaveLength(0)
    })
  })
})