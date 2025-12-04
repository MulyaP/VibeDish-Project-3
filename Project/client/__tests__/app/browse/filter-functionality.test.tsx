import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter, useSearchParams } from 'next/navigation'
import BrowsePage from '@/app/browse/page'
import { useAuth } from '@/context/auth-context'
import { useToast } from '@/hooks/use-toast'

// Mock dependencies
jest.mock('next/navigation')
jest.mock('@/context/auth-context')
jest.mock('@/hooks/use-toast')
jest.mock('@/lib/api', () => ({
  getCart: jest.fn().mockResolvedValue({ items: [] }),
  getMoodRecommendations: jest.fn().mockResolvedValue({ recommended_foods: [] }),
  addToCart: jest.fn(),
  updateCartItem: jest.fn(),
  removeFromCart: jest.fn(),
  checkSpotifyStatus: jest.fn(),
  initiateSpotifyLogin: jest.fn()
}))

const mockRouter = {
  push: jest.fn(),
}

const mockSearchParams = {
  get: jest.fn(),
}

const mockAuth = {
  isAuthenticated: true,
  user: { id: '1', name: 'Test User', role: 'customer' },
  logout: jest.fn(),
}

const mockToast = {
  toast: jest.fn(),
}

// Mock fetch
global.fetch = jest.fn()

describe('Filter Functionality', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(useRouter as jest.Mock).mockReturnValue(mockRouter)
    ;(useSearchParams as jest.Mock).mockReturnValue(mockSearchParams)
    ;(useAuth as jest.Mock).mockReturnValue(mockAuth)
    ;(useToast as jest.Mock).mockReturnValue(mockToast)
    
    mockSearchParams.get.mockReturnValue(null)
    
    // Mock successful API responses
    ;(fetch as jest.Mock).mockImplementation((url) => {
      if (url.includes('/restaurants')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            { id: '1', name: 'Test Restaurant', address: '123 Test St' }
          ])
        })
      }
      if (url.includes('/meals')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            { 
              id: '1', 
              name: 'Vegetarian Pasta', 
              tags: ['vegetarian'], 
              allergens: [],
              base_price: 12.99,
              quantity: 5,
              surplus_price: 9.99,
              calories: 450
            },
            { 
              id: '2', 
              name: 'Vegan Salad', 
              tags: ['vegan', 'vegetarian'], 
              allergens: ['nuts'],
              base_price: 8.99,
              quantity: 3,
              surplus_price: 6.99,
              calories: 250
            }
          ])
        })
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
    })
  })

  describe('Filter Button Visibility', () => {
    it('should show filter button only in meals view', async () => {
      render(<BrowsePage />)
      
      // Should not show filter button in restaurants view
      expect(screen.queryByText('Filters')).not.toBeInTheDocument()
      
      // Click on a restaurant to go to meals view
      await waitFor(() => {
        const restaurant = screen.getByText('Test Restaurant')
        fireEvent.click(restaurant)
      })
      
      // Should show filter button in meals view
      await waitFor(() => {
        expect(screen.getByText('Filters')).toBeInTheDocument()
      })
    })

    it('should show active state when filters are applied', async () => {
      render(<BrowsePage />)
      
      // Navigate to meals view
      await waitFor(() => {
        fireEvent.click(screen.getByText('Test Restaurant'))
      })
      
      // Open filters
      await waitFor(() => {
        fireEvent.click(screen.getByText('Filters'))
      })
      
      // Select vegetarian filter
      const vegetarianCheckbox = screen.getByLabelText('Vegetarian')
      fireEvent.click(vegetarianCheckbox)
      
      // Apply filters
      fireEvent.click(screen.getByText('Apply Filters'))
      
      // Filter button should show active state
      await waitFor(() => {
        const filterButton = screen.getByText('Filters')
        expect(filterButton.closest('button')).toHaveClass('bg-primary')
      })
    })
  })

  describe('Filter Panel Functionality', () => {
    beforeEach(async () => {
      render(<BrowsePage />)
      
      // Navigate to meals view
      await waitFor(() => {
        fireEvent.click(screen.getByText('Test Restaurant'))
      })
      
      // Open filters
      await waitFor(() => {
        fireEvent.click(screen.getByText('Filters'))
      })
    })

    it('should show all filter options when panel is open', () => {
      expect(screen.getByLabelText('Vegetarian')).toBeInTheDocument()
      expect(screen.getByLabelText('Vegan')).toBeInTheDocument()
      expect(screen.getByLabelText('Gluten Free')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('e.g., nuts, dairy, shellfish')).toBeInTheDocument()
    })

    it('should allow selecting dietary preferences', () => {
      const vegetarianCheckbox = screen.getByLabelText('Vegetarian')
      const veganCheckbox = screen.getByLabelText('Vegan')
      
      fireEvent.click(vegetarianCheckbox)
      fireEvent.click(veganCheckbox)
      
      expect(vegetarianCheckbox).toBeChecked()
      expect(veganCheckbox).toBeChecked()
    })

    it('should allow entering allergen exclusions', () => {
      const allergenInput = screen.getByPlaceholderText('e.g., nuts, dairy, shellfish')
      
      fireEvent.change(allergenInput, { target: { value: 'nuts, dairy' } })
      
      expect(allergenInput).toHaveValue('nuts, dairy')
    })
  })

  describe('Filter Actions', () => {
    beforeEach(async () => {
      render(<BrowsePage />)
      
      // Navigate to meals view and open filters
      await waitFor(() => {
        fireEvent.click(screen.getByText('Test Restaurant'))
      })
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Filters'))
      })
    })

    it('should apply filters and close panel when Apply Filters is clicked', async () => {
      const vegetarianCheckbox = screen.getByLabelText('Vegetarian')
      fireEvent.click(vegetarianCheckbox)
      
      fireEvent.click(screen.getByText('Apply Filters'))
      
      // Panel should close
      await waitFor(() => {
        expect(screen.queryByText('Dietary Preferences')).not.toBeInTheDocument()
      })
      
      // Filter button should show active state
      await waitFor(() => {
        const filterButton = screen.getByText('Filters')
        expect(filterButton.closest('button')).toHaveClass('bg-primary')
      })
    })

    it('should clear filters and close panel when Clear is clicked', async () => {
      // Set some filters first
      fireEvent.click(screen.getByLabelText('Vegetarian'))
      fireEvent.change(screen.getByPlaceholderText('e.g., nuts, dairy, shellfish'), { 
        target: { value: 'nuts' } 
      })
      
      fireEvent.click(screen.getByText('Clear'))
      
      // Panel should close
      await waitFor(() => {
        expect(screen.queryByText('Dietary Preferences')).not.toBeInTheDocument()
      })
      
      // Filter button should not show active state
      await waitFor(() => {
        const filterButton = screen.getByText('Filters')
        expect(filterButton.closest('button')).not.toHaveClass('bg-primary')
      })
    })

    it('should cancel changes and close panel when Cancel is clicked', async () => {
      // Make some temporary changes
      fireEvent.click(screen.getByLabelText('Vegetarian'))
      
      fireEvent.click(screen.getByText('Cancel'))
      
      // Panel should close
      await waitFor(() => {
        expect(screen.queryByText('Dietary Preferences')).not.toBeInTheDocument()
      })
      
      // Changes should not be applied (no new API call)
      const fetchCalls = (fetch as jest.Mock).mock.calls
      const lastCall = fetchCalls[fetchCalls.length - 1]
      expect(lastCall[0]).not.toContain('vegetarian=true')
    })
  })

  describe('API Integration', () => {
    it('should apply frontend filtering correctly', async () => {
      render(<BrowsePage />)
      
      // Navigate to meals view
      await waitFor(() => {
        fireEvent.click(screen.getByText('Test Restaurant'))
      })
      
      // Open filters and set vegetarian filter
      await waitFor(() => {
        fireEvent.click(screen.getByText('Filters'))
      })
      
      fireEvent.click(screen.getByLabelText('Vegetarian'))
      fireEvent.click(screen.getByText('Apply Filters'))
      
      // Filter should be applied (button shows active state)
      await waitFor(() => {
        const filterButton = screen.getByText('Filters')
        expect(filterButton.closest('button')).toHaveClass('bg-primary')
      })
    })

    it('should handle API errors gracefully', async () => {
      // Mock API error for restaurants fetch
      ;(fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'))
      
      render(<BrowsePage />)
      
      // Should show error message
      await waitFor(() => {
        expect(screen.getByText(/Error:/)).toBeInTheDocument()
      })
    })
  })

  describe('Filter State Management', () => {
    it('should reset filters when switching restaurants', async () => {
      // Mock multiple restaurants
      ;(fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/restaurants')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve([
              { id: '1', name: 'Restaurant 1', address: '123 Test St' },
              { id: '2', name: 'Restaurant 2', address: '456 Test Ave' }
            ])
          })
        }
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
      })
      
      render(<BrowsePage />)
      
      // Navigate to first restaurant and set filters
      await waitFor(() => {
        fireEvent.click(screen.getByText('Restaurant 1'))
      })
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Filters'))
      })
      
      fireEvent.click(screen.getByLabelText('Vegetarian'))
      fireEvent.click(screen.getByText('Apply Filters'))
      
      // Go back and select different restaurant
      fireEvent.click(screen.getByText('Back to Restaurants'))
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Restaurant 2'))
      })
      
      // Filters should be reset
      await waitFor(() => {
        fireEvent.click(screen.getByText('Filters'))
      })
      
      expect(screen.getByLabelText('Vegetarian')).not.toBeChecked()
    })
  })
})