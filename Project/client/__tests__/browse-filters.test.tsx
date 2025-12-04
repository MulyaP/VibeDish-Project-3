// Simple test for filter logic without component rendering

// Test data
const mockMeals = [
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

// Filter function extracted from component
const filterMeals = (meals: any[], filters: any, searchQuery = '') => {
  return meals.filter((meal) => {
    const matchesSearch = meal.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      meal.tags.some((tag: string) => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    
    const matchesVegetarian = !filters.vegetarian || meal.tags.some((tag: string) => tag.toLowerCase().includes('vegetarian'))
    const matchesVegan = !filters.vegan || meal.tags.some((tag: string) => tag.toLowerCase().includes('vegan'))
    const matchesGlutenFree = !filters.gluten_free || meal.tags.some((tag: string) => tag.toLowerCase().includes('gluten') && tag.toLowerCase().includes('free'))
    
    const matchesAllergens = !filters.exclude_allergens || 
      !meal.allergens.some((allergen: string) => 
        filters.exclude_allergens.toLowerCase().split(',').some((excluded: string) => 
          allergen.toLowerCase().includes(excluded.trim())
        )
      )
    
    return matchesSearch && matchesVegetarian && matchesVegan && matchesGlutenFree && matchesAllergens
  })
}

describe('Browse Page Filter Logic', () => {
  describe('Filter Logic', () => {
    test('vegetarian filter shows only vegetarian meals', () => {
      const filters = { vegetarian: true, vegan: false, gluten_free: false, exclude_allergens: '' }
      const result = filterMeals(mockMeals, filters)
      
      expect(result).toHaveLength(1)
      expect(result[0].name).toBe('Veggie Burger')
    })

    test('vegan filter shows only vegan meals', () => {
      const filters = { vegetarian: false, vegan: true, gluten_free: false, exclude_allergens: '' }
      const result = filterMeals(mockMeals, filters)
      
      expect(result).toHaveLength(1)
      expect(result[0].name).toBe('Vegan Salad')
    })

    test('gluten free filter shows only gluten free meals', () => {
      const filters = { vegetarian: false, vegan: false, gluten_free: true, exclude_allergens: '' }
      const result = filterMeals(mockMeals, filters)
      
      expect(result).toHaveLength(1)
      expect(result[0].name).toBe('Vegan Salad')
    })

    test('exclude allergens filter hides meals with specified allergens', () => {
      const filters = { vegetarian: false, vegan: false, gluten_free: false, exclude_allergens: 'gluten' }
      const result = filterMeals(mockMeals, filters)
      
      expect(result).toHaveLength(1)
      expect(result[0].name).toBe('Vegan Salad')
    })

    test('no filters shows all meals', () => {
      const filters = { vegetarian: false, vegan: false, gluten_free: false, exclude_allergens: '' }
      const result = filterMeals(mockMeals, filters)
      
      expect(result).toHaveLength(3)
    })

    test('search query works', () => {
      const filters = { vegetarian: false, vegan: false, gluten_free: false, exclude_allergens: '' }
      const result = filterMeals(mockMeals, filters, 'salad')
      
      expect(result).toHaveLength(1)
      expect(result[0].name).toBe('Vegan Salad')
    })
  })
})