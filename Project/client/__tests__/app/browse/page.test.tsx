import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useSearchParams, useRouter } from 'next/navigation'
import BrowsePage from '@/app/browse/page'
import { useAuth } from '@/context/auth-context'
import * as api from '@/lib/api'

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}))

jest.mock('@/context/auth-context', () => ({
  useAuth: jest.fn(),
}))

jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}))

jest.mock('@/lib/api', () => ({
  addToCart: jest.fn(),
  getCart: jest.fn(),
  updateCartItem: jest.fn(),
  removeFromCart: jest.fn(),
  getMoodRecommendations: jest.fn(),
  checkSpotifyStatus: jest.fn(),
  initiateSpotifyLogin: jest.fn(),
}))

global.fetch = jest.fn()

// Mock console methods to prevent test failures
const originalWarn = console.warn
const originalError = console.error
beforeAll(() => {
  console.warn = jest.fn()
  console.error = jest.fn()
})
afterAll(() => {
  console.warn = originalWarn
  console.error = originalError
})

describe('BrowsePage', () => {
  const mockPush = jest.fn()
  const mockGet = jest.fn()
  const mockRouter = {
    push: mockPush,
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }

  const mockRestaurants = [
    {
      id: '1',
      name: 'Pizza Palace',
      address: '123 Main St',
      owner_id: 'owner1',
      created_at: '2024-01-01',
    },
    {
      id: '2', 
      name: 'Burger Barn',
      address: '456 Oak Ave',
      owner_id: 'owner2',
      created_at: '2024-01-02',
    }
  ]

  const mockMeals = [
    {
      id: 'meal1',
      restaurant_id: '1',
      name: 'Margherita Pizza',
      tags: ['vegetarian', 'italian'],
      base_price: 15.99,
      quantity: 5,
      surplus_price: 9.99,
      allergens: ['gluten', 'dairy'],
      calories: 800,
      created_at: '2024-01-01',
    },
    {
      id: 'meal2',
      restaurant_id: '1', 
      name: 'Pepperoni Pizza',
      tags: ['italian'],
      base_price: 17.99,
      quantity: 0,
      surplus_price: null,
      allergens: ['gluten', 'dairy'],
      calories: 950,
      created_at: '2024-01-01',
    }
  ]

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useRouter as jest.Mock).mockReturnValue(mockRouter)
    ;(useSearchParams as jest.Mock).mockReturnValue({
      get: mockGet,
    })
    mockGet.mockReturnValue(null)
    ;(global.fetch as jest.Mock).mockClear()
    ;(useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
    })
    ;(api.getCart as jest.Mock).mockResolvedValue({
      cart_id: 'cart-1',
      items: [],
      cart_total: 0,
    })
  })

  describe('Restaurant View', () => {
    it('renders restaurants page header', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockRestaurants,
      })

      render(<BrowsePage />)

      await waitFor(() => {
        expect(screen.getByText('Browse Restaurants')).toBeInTheDocument()
      })
    })

    it('displays restaurants after loading', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockRestaurants,
      })

      render(<BrowsePage />)

      await waitFor(() => {
        expect(screen.getByText('Pizza Palace')).toBeInTheDocument()
        expect(screen.getByText('Burger Barn')).toBeInTheDocument()
      })
    })

    it('shows loading state', () => {
      ;(global.fetch as jest.Mock).mockImplementationOnce(
        () => new Promise(() => {})
      )

      const { container } = render(<BrowsePage />)
      
      const loader = container.querySelector('.animate-spin')
      expect(loader).toBeInTheDocument()
    })

    it('handles restaurant search', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockRestaurants,
      })

      render(<BrowsePage />)

      await waitFor(() => {
        expect(screen.getByText('Pizza Palace')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText('Search restaurants...')
      fireEvent.change(searchInput, { target: { value: 'Pizza' } })

      await waitFor(() => {
        expect(screen.getByText('Pizza Palace')).toBeInTheDocument()
        expect(screen.queryByText('Burger Barn')).not.toBeInTheDocument()
      })
    })

    it('handles fetch error', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
      })

      render(<BrowsePage />)

      await waitFor(() => {
        expect(screen.getByText(/Error:/)).toBeInTheDocument()
      })
    })
  })

  describe('Meals View', () => {
    beforeEach(async () => {
      ;(global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockRestaurants,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockMeals,
        })
    })

    it('switches to meals view when restaurant clicked', async () => {
      render(<BrowsePage />)

      await waitFor(() => {
        const restaurant = screen.getByText('Pizza Palace')
        fireEvent.click(restaurant)
      })

      await waitFor(() => {
        expect(screen.getByText('Back to Restaurants')).toBeInTheDocument()
      })
    })

    it('displays meals for selected restaurant', async () => {
      render(<BrowsePage />)

      await waitFor(() => {
        const restaurant = screen.getByText('Pizza Palace')
        fireEvent.click(restaurant)
      })

      await waitFor(() => {
        expect(screen.getByText('Margherita Pizza')).toBeInTheDocument()
        expect(screen.getByText('Pepperoni Pizza')).toBeInTheDocument()
      })
    })

    it('shows surplus meals section', async () => {
      render(<BrowsePage />)

      await waitFor(() => {
        const restaurant = screen.getByText('Pizza Palace')
        fireEvent.click(restaurant)
      })

      await waitFor(() => {
        expect(screen.getByText(/Surplus Meals/)).toBeInTheDocument()
      })
    })

    it('displays meal details correctly', async () => {
      render(<BrowsePage />)

      await waitFor(() => {
        const restaurant = screen.getByText('Pizza Palace')
        fireEvent.click(restaurant)
      })

      await waitFor(() => {
        expect(screen.getAllByText('gluten, dairy')[0]).toBeInTheDocument()
        expect(screen.getByText('$9.99')).toBeInTheDocument()
        expect(screen.getByText('$15.99')).toBeInTheDocument()
      })
    })

    it('shows sold out for zero quantity meals', async () => {
      render(<BrowsePage />)

      await waitFor(() => {
        const restaurant = screen.getByText('Pizza Palace')
        fireEvent.click(restaurant)
      })

      await waitFor(() => {
        expect(screen.getByText('Sold Out')).toBeInTheDocument()
      })
    })

    it('returns to restaurants view when back clicked', async () => {
      render(<BrowsePage />)

      await waitFor(() => {
        const restaurant = screen.getByText('Pizza Palace')
        fireEvent.click(restaurant)
      })

      await waitFor(() => {
        const backButton = screen.getByText('Back to Restaurants')
        fireEvent.click(backButton)
      })

      await waitFor(() => {
        expect(screen.getByText('Browse Restaurants')).toBeInTheDocument()
      })
    })
  })

  describe('Filters', () => {
    beforeEach(async () => {
      ;(global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockRestaurants,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockMeals,
        })
    })

    it('opens filter panel', async () => {
      render(<BrowsePage />)

      await waitFor(() => {
        const restaurant = screen.getByText('Pizza Palace')
        fireEvent.click(restaurant)
      })

      await waitFor(() => {
        const filtersButton = screen.getByText('Filters')
        fireEvent.click(filtersButton)
      })

      await waitFor(() => {
        expect(screen.getByText('Dietary Preferences')).toBeInTheDocument()
      })
    })

    it('applies vegetarian filter', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockMeals.filter(m => m.tags.includes('vegetarian')),
      })

      render(<BrowsePage />)

      await waitFor(() => {
        const restaurant = screen.getByText('Pizza Palace')
        fireEvent.click(restaurant)
      })

      await waitFor(() => {
        const filtersButton = screen.getByText('Filters')
        fireEvent.click(filtersButton)
      })

      await waitFor(() => {
        const vegetarianCheckbox = screen.getByLabelText('Vegetarian')
        fireEvent.click(vegetarianCheckbox)
        
        const applyButton = screen.getByText('Apply Filters')
        fireEvent.click(applyButton)
      })

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('vegetarian=true')
        )
      })
    })
  })

  describe('Cart Operations', () => {
    beforeEach(() => {
      ;(useAuth as jest.Mock).mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: { id: 'user1' },
      })
      ;(global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockRestaurants,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockMeals,
        })
    })

    it('adds item to cart', async () => {
      ;(api.addToCart as jest.Mock).mockResolvedValueOnce({
        items: [{ meal_id: 'meal1', qty: 1, item_id: 'item1' }]
      })

      render(<BrowsePage />)

      await waitFor(() => {
        const restaurant = screen.getByText('Pizza Palace')
        fireEvent.click(restaurant)
      })

      await waitFor(() => {
        const addButtons = screen.getAllByRole('button')
        const plusButton = addButtons.find(btn =>
          btn.querySelector('svg')?.classList.contains('lucide-plus')
        )
        if (plusButton) {
          fireEvent.click(plusButton)
        }
      })

      await waitFor(() => {
        expect(api.addToCart).toHaveBeenCalledWith('meal1', 1)
      })
    })

    it('handles cart errors', async () => {
      ;(api.addToCart as jest.Mock).mockRejectedValueOnce(new Error('Cart error'))

      render(<BrowsePage />)

      await waitFor(() => {
        const restaurant = screen.getByText('Pizza Palace')
        fireEvent.click(restaurant)
      })

      await waitFor(() => {
        const addButtons = screen.getAllByRole('button')
        const plusButton = addButtons.find(btn =>
          btn.querySelector('svg')?.classList.contains('lucide-plus')
        )
        if (plusButton) {
          fireEvent.click(plusButton)
        }
      })

      await waitFor(() => {
        expect(api.getCart).toHaveBeenCalled()
      })
    })
  })

  describe('Spotify Integration', () => {
    beforeEach(() => {
      ;(useAuth as jest.Mock).mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: { id: 'user1' },
      })
      ;(global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockRestaurants,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockMeals,
        })
    })

    it('shows Spotify connect when recommendations fail', async () => {
      ;(api.getMoodRecommendations as jest.Mock).mockRejectedValueOnce({
        status: 404,
        message: 'User Spotify authentication not found'
      })

      render(<BrowsePage />)

      await waitFor(() => {
        const restaurant = screen.getByText('Pizza Palace')
        fireEvent.click(restaurant)
      })

      await waitFor(() => {
        expect(screen.getByText('Get Personalized Recommendations')).toBeInTheDocument()
      })
    })

    it('shows recommendations when available', async () => {
      ;(api.getMoodRecommendations as jest.Mock).mockResolvedValueOnce({
        recommended_foods: [{ id: 'meal1' }]
      })

      render(<BrowsePage />)

      await waitFor(() => {
        const restaurant = screen.getByText('Pizza Palace')
        fireEvent.click(restaurant)
      })

      await waitFor(() => {
        expect(screen.getByText('Perfect for Your Mood')).toBeInTheDocument()
      })
    })
  })

  describe('URL Parameters', () => {
    it('loads meals view from URL parameter', async () => {
      mockGet.mockReturnValue('1')
      ;(global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockRestaurants,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockMeals,
        })

      render(<BrowsePage />)

      await waitFor(() => {
        expect(screen.getByText('Back to Restaurants')).toBeInTheDocument()
      })
    })
  })

  describe('Edge Cases', () => {
    it('handles empty restaurants', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      })

      render(<BrowsePage />)

      await waitFor(() => {
        expect(screen.getByText('Showing 0 restaurants')).toBeInTheDocument()
      })
    })

    it('handles empty meals', async () => {
      ;(global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockRestaurants,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [],
        })

      render(<BrowsePage />)

      await waitFor(() => {
        const restaurant = screen.getByText('Pizza Palace')
        fireEvent.click(restaurant)
      })

      await waitFor(() => {
        expect(screen.getByText('No meals found for this restaurant')).toBeInTheDocument()
      })
    })

    it('handles network errors', async () => {
      ;(global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      )

      render(<BrowsePage />)

      await waitFor(() => {
        expect(screen.getByText(/Network error/)).toBeInTheDocument()
      })
    })
  })
})