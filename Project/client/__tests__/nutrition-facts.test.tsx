import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { NutritionFacts } from '@/components/nutrition-facts'
import '@testing-library/jest-dom'

// Mock fetch
global.fetch = jest.fn()

describe('NutritionFacts Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders the nutrition facts button', () => {
    render(<NutritionFacts mealId="test-meal-id" mealName="Test Meal" />)
    
    const button = screen.getByRole('button', { name: /nutrition facts/i })
    expect(button).toBeInTheDocument()
  })

  it('opens dialog when button is clicked', async () => {
    const mockData = {
      meal_name: 'Test Meal',
      calories: 200,
      protein_g: 10.0,
      carbs_g: 20.0,
      fat_g: 5.0,
      fiber_g: 2.0,
      sugar_g: 3.0,
      sodium_mg: 300.0,
      source: 'estimate'
    }

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    })

    render(<NutritionFacts mealId="test-meal-id" mealName="Test Meal" />)
    
    const button = screen.getByRole('button', { name: /nutrition facts/i })
    fireEvent.click(button)
    
    // Wait for data to load instead of just dialog title
    await waitFor(() => {
      expect(screen.getByText('200')).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('displays loading state while fetching data', async () => {
    ;(global.fetch as jest.Mock).mockImplementation(() => 
      new Promise(resolve => setTimeout(resolve, 100))
    )

    render(<NutritionFacts mealId="test-meal-id" mealName="Test Meal" />)
    
    const button = screen.getByRole('button', { name: /nutrition facts/i })
    fireEvent.click(button)
    
    await waitFor(() => {
      expect(screen.getByText(/loading nutrition data/i)).toBeInTheDocument()
    })
  })

  it('displays nutrition data from FatSecret API', async () => {
    const mockData = {
      meal_name: 'Chicken Breast',
      serving_size: '100g',
      calories: 165,
      protein_g: 31.0,
      carbs_g: 0.0,
      fat_g: 3.6,
      fiber_g: 0.0,
      sugar_g: 0.0,
      sodium_mg: 74.0,
      source: 'fatsecret_api',
      source_message: 'Matched: Chicken Breast',
      food_url: 'https://fatsecret.com/chicken'
    }

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    })

    render(<NutritionFacts mealId="test-meal-id" mealName="Chicken Breast" />)
    
    const button = screen.getByRole('button', { name: /nutrition facts/i })
    fireEvent.click(button)
    
    await waitFor(() => {
      expect(screen.getByText('165')).toBeInTheDocument()
      expect(screen.getByText('✓ FatSecret API Data')).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('displays estimated data when API returns estimates', async () => {
    const mockData = {
      meal_name: 'Unknown Meal',
      calories: 250,
      protein_g: 15.0,
      carbs_g: 25.0,
      fat_g: 10.0,
      fiber_g: 3.0,
      sugar_g: 5.0,
      sodium_mg: 400.0,
      source: 'estimate',
      source_message: 'No API match found'
    }

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    })

    render(<NutritionFacts mealId="test-meal-id" mealName="Unknown Meal" />)
    
    const button = screen.getByRole('button', { name: /nutrition facts/i })
    fireEvent.click(button)
    
    await waitFor(() => {
      expect(screen.getByText('250')).toBeInTheDocument()
      expect(screen.getByText('⚠ Estimated Data')).toBeInTheDocument()
      expect(screen.getByText('No API match found')).toBeInTheDocument()
    })
  })

  it('displays link to FatSecret when API data is available', async () => {
    const mockData = {
      meal_name: 'Pizza',
      calories: 285,
      protein_g: 12.0,
      carbs_g: 36.0,
      fat_g: 10.0,
      fiber_g: 2.5,
      sugar_g: 4.0,
      sodium_mg: 640.0,
      source: 'fatsecret_api',
      source_message: 'Matched: Pizza',
      food_url: 'https://fatsecret.com/pizza'
    }

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    })

    render(<NutritionFacts mealId="test-meal-id" mealName="Pizza" />)
    
    const button = screen.getByRole('button', { name: /nutrition facts/i })
    fireEvent.click(button)
    
    await waitFor(() => {
      const link = screen.getByText(/view detailed nutrition info/i)
      expect(link).toBeInTheDocument()
      expect(link).toHaveAttribute('href', 'https://fatsecret.com/pizza')
      expect(link).toHaveAttribute('target', '_blank')
    })
  })

  it('does not display link when using estimated data', async () => {
    const mockData = {
      meal_name: 'Generic Meal',
      calories: 250,
      protein_g: 15.0,
      carbs_g: 25.0,
      fat_g: 10.0,
      fiber_g: 3.0,
      sugar_g: 5.0,
      sodium_mg: 400.0,
      source: 'estimate'
    }

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    })

    render(<NutritionFacts mealId="test-meal-id" mealName="Generic Meal" />)
    
    const button = screen.getByRole('button', { name: /nutrition facts/i })
    fireEvent.click(button)
    
    await waitFor(() => {
      expect(screen.queryByText(/view detailed nutrition info/i)).not.toBeInTheDocument()
    })
  })

  it('displays error message when fetch fails', async () => {
    ;(global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))

    render(<NutritionFacts mealId="test-meal-id" mealName="Test Meal" />)
    
    const button = screen.getByRole('button', { name: /nutrition facts/i })
    fireEvent.click(button)
    
    await waitFor(() => {
      expect(screen.getByText(/failed to load nutrition data/i)).toBeInTheDocument()
    })
  })

  it('displays all nutrient rows', async () => {
    const mockData = {
      meal_name: 'Complete Meal',
      calories: 500,
      protein_g: 30.0,
      carbs_g: 50.0,
      fat_g: 20.0,
      fiber_g: 10.0,
      sugar_g: 15.0,
      sodium_mg: 800.0,
      source: 'fatsecret_api'
    }

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    })

    render(<NutritionFacts mealId="test-meal-id" mealName="Complete Meal" />)
    
    const button = screen.getByRole('button', { name: /nutrition facts/i })
    fireEvent.click(button)
    
    await waitFor(() => {
      expect(screen.getByText('Protein')).toBeInTheDocument()
      expect(screen.getByText('Carbohydrates')).toBeInTheDocument()
      expect(screen.getByText('Fat')).toBeInTheDocument()
      expect(screen.getByText('Fiber')).toBeInTheDocument()
      expect(screen.getByText('Sugar')).toBeInTheDocument()
      expect(screen.getByText('Sodium')).toBeInTheDocument()
    })
  })

  it('only fetches data once when dialog is opened', async () => {
    const mockData = {
      meal_name: 'Test Meal',
      calories: 200,
      protein_g: 10.0,
      carbs_g: 20.0,
      fat_g: 5.0,
      fiber_g: 2.0,
      sugar_g: 3.0,
      sodium_mg: 300.0,
      source: 'fatsecret_api'
    }

    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => mockData
    })

    render(<NutritionFacts mealId="test-meal-id" mealName="Test Meal" />)
    
    const button = screen.getByRole('button', { name: /nutrition facts/i })
    
    // Open dialog
    fireEvent.click(button)
    await waitFor(() => expect(screen.getByText('200')).toBeInTheDocument())
    
    // Close dialog
    const closeButton = screen.getByRole('button', { name: /close/i })
    fireEvent.click(closeButton)
    
    // Open again
    fireEvent.click(button)
    await waitFor(() => expect(screen.getByText('200')).toBeInTheDocument())
    
    // Should only fetch once
    expect(global.fetch).toHaveBeenCalledTimes(1)
  })
})
