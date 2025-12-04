import { render, screen, waitFor } from '@testing-library/react'
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

const mockRouter = { push: jest.fn() }
const mockAuth = { isAuthenticated: true, user: { id: '1', name: 'Test User', role: 'customer' } }
const mockToast = { toast: jest.fn() }

global.fetch = jest.fn()

describe('BrowsePage URL Handling', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(useRouter as jest.Mock).mockReturnValue(mockRouter)
    ;(useAuth as jest.Mock).mockReturnValue(mockAuth)
    ;(useToast as jest.Mock).mockReturnValue(mockToast)
    
    // Mock successful API responses
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
      if (url.includes('/meals')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            { 
              id: '1', 
              name: 'Test Meal', 
              tags: ['vegetarian'], 
              allergens: [],
              base_price: 12.99,
              quantity: 5,
              surplus_price: 9.99,
              calories: 450
            }
          ])
        })
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
    })
  })

  describe('Restaurant URL Parameter', () => {
    it('should load restaurant from URL parameter', async () => {
      const mockSearchParams = {
        get: jest.fn().mockImplementation((param) => {
          if (param === 'restaurant') return '1'
          return null
        })
      }
      ;(useSearchParams as jest.Mock).mockReturnValue(mockSearchParams)

      render(<BrowsePage />)
      
      // Should automatically navigate to meals view for restaurant 1
      await waitFor(() => {
        expect(screen.getByText('Restaurant 1')).toBeInTheDocument()
      })
    })

    it('should handle invalid restaurant ID in URL', async () => {
      const mockSearchParams = {
        get: jest.fn().mockImplementation((param) => {
          if (param === 'restaurant') return 'invalid-id'
          return null
        })
      }
      ;(useSearchParams as jest.Mock).mockReturnValue(mockSearchParams)

      render(<BrowsePage />)
      
      // Should stay in restaurants view since invalid ID won't match
      await waitFor(() => {
        expect(screen.getByText('Browse Restaurants')).toBeInTheDocument()
      })
    })

    it('should reset to restaurants view when URL parameter is removed', async () => {
      const mockSearchParams = {
        get: jest.fn().mockImplementation((param) => {
          if (param === 'restaurant') return null // No restaurant parameter
          return null
        })
      }
      ;(useSearchParams as jest.Mock).mockReturnValue(mockSearchParams)

      render(<BrowsePage />)
      
      await waitFor(() => {
        expect(screen.getByText('Browse Restaurants')).toBeInTheDocument()
      })
    })
  })

  describe('Back Navigation', () => {
    it('should navigate to /browse when back button clicked with URL parameter', async () => {
      const mockSearchParams = {
        get: jest.fn().mockImplementation((param) => {
          if (param === 'restaurant') return '1'
          return null
        })
      }
      ;(useSearchParams as jest.Mock).mockReturnValue(mockSearchParams)

      render(<BrowsePage />)
      
      // Wait for the component to load the restaurant and switch to meals view
      await waitFor(() => {
        expect(screen.getByText('Restaurant 1')).toBeInTheDocument()
      })
      
      // Wait for the meals view to be displayed (should show the back button)
      await waitFor(() => {
        expect(screen.getByText('Back to Restaurants')).toBeInTheDocument()
      })

      const backButton = screen.getByText('Back to Restaurants')
      backButton.click()

      expect(mockRouter.push).toHaveBeenCalledWith('/browse')
    })
  })

  describe('Filter State Reset', () => {
    it('should reset filters when switching restaurants', async () => {
      const mockSearchParams = {
        get: jest.fn().mockReturnValue(null)
      }
      ;(useSearchParams as jest.Mock).mockReturnValue(mockSearchParams)

      render(<BrowsePage />)
      
      // Wait for restaurants to load
      await waitFor(() => {
        expect(screen.getByText('Restaurant 1')).toBeInTheDocument()
      })

      // Click on first restaurant
      screen.getByText('Restaurant 1').click()

      await waitFor(() => {
        expect(screen.getByText('Filters')).toBeInTheDocument()
      })

      // Filters should be reset (no active state)
      const filterButton = screen.getByText('Filters')
      expect(filterButton.closest('button')).not.toHaveClass('bg-primary')
    })
  })
})