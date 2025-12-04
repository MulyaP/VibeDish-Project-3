import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import OwnerDashboard from '@/app/owner/page'
import * as api from '@/lib/api'

jest.mock('@/lib/api', () => ({
  getMyRestaurant: jest.fn(),
  getOwnerMeals: jest.fn(),
  createMeal: jest.fn(),
  updateMeal: jest.fn(),
  deleteMeal: jest.fn(),
  getPresignedUploadUrl: jest.fn(),
  uploadFileToS3: jest.fn(),
  deleteImageFromS3: jest.fn(),
}))

jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}))

// Mock URL.createObjectURL and URL.revokeObjectURL
global.URL.createObjectURL = jest.fn(() => 'mock-url')
global.URL.revokeObjectURL = jest.fn()

describe('OwnerDashboard', () => {
  const mockRestaurant = {
    id: '1',
    name: 'Test Restaurant',
    address: '123 Test St',
    owner_id: 'owner1',
  }

  const mockMeals = [
    {
      id: 'meal1',
      restaurant_id: '1',
      name: 'Test Meal 1',
      tags: ['vegetarian', 'healthy'],
      base_price: 15.99,
      quantity: 10,
      surplus_price: 9.99,
      allergens: ['gluten'],
      calories: 500,
      image_link: 'https://example.com/image1.jpg',
    },
    {
      id: 'meal2',
      restaurant_id: '1',
      name: 'Test Meal 2',
      tags: ['vegan'],
      base_price: 12.99,
      quantity: 0,
      surplus_price: null,
      allergens: [],
      calories: 400,
      image_link: null,
    },
  ]

  beforeEach(() => {
    jest.clearAllMocks()
    ;(api.getMyRestaurant as jest.Mock).mockResolvedValue(mockRestaurant)
    ;(api.getOwnerMeals as jest.Mock).mockResolvedValue(mockMeals)
  })

  describe('Initial Rendering', () => {
    it('renders dashboard header', async () => {
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText('Test Restaurant')).toBeInTheDocument()
        expect(screen.getByText('123 Test St')).toBeInTheDocument()
        expect(screen.getByText('Manage your surplus inventory')).toBeInTheDocument()
      })
    })

    it('renders add meal button', async () => {
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText('Add Meal')).toBeInTheDocument()
      })
    })

    it('displays total meals stats', async () => {
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText('Total Meals')).toBeInTheDocument()
        expect(screen.getByText('2')).toBeInTheDocument()
        expect(screen.getByText('10 items in stock')).toBeInTheDocument()
      })
    })

    it('displays meals list', async () => {
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText('Test Meal 1')).toBeInTheDocument()
        expect(screen.getByText('Test Meal 2')).toBeInTheDocument()
        expect(screen.getByText('Out of Stock')).toBeInTheDocument()
      })
    })

    it('shows loading state initially', () => {
      render(<OwnerDashboard />)
      expect(screen.getByText('Loading meals...')).toBeInTheDocument()
    })
  })

  describe('Restaurant Loading', () => {
    it('handles restaurant loading error gracefully', async () => {
      ;(api.getMyRestaurant as jest.Mock).mockRejectedValue(new Error('Failed to load'))
      
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText('Restaurant Dashboard')).toBeInTheDocument()
      })
    })

    it('displays fallback when no restaurant name', async () => {
      ;(api.getMyRestaurant as jest.Mock).mockResolvedValue({ name: '', address: '' })
      
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText('Restaurant Dashboard')).toBeInTheDocument()
      })
    })
  })

  describe('Meals Loading', () => {
    it('handles meals loading error', async () => {
      ;(api.getOwnerMeals as jest.Mock).mockRejectedValue(new Error('Failed to load meals'))
      
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        expect(api.getOwnerMeals).toHaveBeenCalled()
      })
    })

    it('shows empty state when no meals', async () => {
      ;(api.getOwnerMeals as jest.Mock).mockResolvedValue([])
      
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText('No meals added yet. Click "Add Meal" to get started.')).toBeInTheDocument()
      })
    })
  })

  describe('Add Meal Dialog', () => {
    it('opens add meal dialog', async () => {
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        const addButton = screen.getByRole('button', { name: /add meal/i })
        fireEvent.click(addButton)
      })
      
      expect(screen.getByText('Add New Meal')).toBeInTheDocument()
      expect(screen.getByLabelText(/Meal Name/)).toBeInTheDocument()
    })

    it('fills and submits add meal form', async () => {
      ;(api.createMeal as jest.Mock).mockResolvedValue({})
      
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /add meal/i }))
      })
      
      // Fill form
      fireEvent.change(screen.getByLabelText(/Meal Name/), { target: { value: 'New Meal' } })
      fireEvent.change(screen.getByLabelText(/Base Price/), { target: { value: '10.99' } })
      fireEvent.change(screen.getByLabelText(/Quantity/), { target: { value: '5' } })
      
      // Submit
      fireEvent.click(screen.getAllByText('Add Meal')[1])
      
      await waitFor(() => {
        expect(api.createMeal).toHaveBeenCalledWith({
          name: 'New Meal',
          base_price: 10.99,
          quantity: 5,
          tags: undefined,
          surplus_price: undefined,
          allergens: undefined,
          calories: undefined,
          image_link: undefined,
        })
      })
    })

    it('validates required fields', async () => {
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /add meal/i }))
      })
      
      // Try to submit without required fields
      fireEvent.click(screen.getAllByText('Add Meal')[1])
      
      // Should not call API
      expect(api.createMeal).not.toHaveBeenCalled()
    })

    it('handles form submission error', async () => {
      ;(api.createMeal as jest.Mock).mockRejectedValue(new Error('Failed to create'))
      
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /add meal/i }))
      })
      
      // Fill required fields
      fireEvent.change(screen.getByLabelText(/Meal Name/), { target: { value: 'New Meal' } })
      fireEvent.change(screen.getByLabelText(/Base Price/), { target: { value: '10.99' } })
      fireEvent.change(screen.getByLabelText(/Quantity/), { target: { value: '5' } })
      
      fireEvent.click(screen.getAllByText('Add Meal')[1])
      
      await waitFor(() => {
        expect(api.createMeal).toHaveBeenCalled()
      })
    })

    it('cancels add meal dialog', async () => {
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /add meal/i }))
      })
      
      fireEvent.click(screen.getByRole('button', { name: /cancel/i }))
      
      await waitFor(() => {
        expect(screen.queryByText('Add New Meal')).not.toBeInTheDocument()
      })
    })
  })

  describe('Meal Actions', () => {
    it('renders edit and delete buttons for each meal', async () => {
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        // Wait for meals to be loaded and displayed
        expect(screen.getByText('Test Meal 1')).toBeInTheDocument()
        expect(screen.getByText('Test Meal 2')).toBeInTheDocument()
        
        // Count all buttons - should have Add Meal + Edit + Delete buttons for each meal
        const allButtons = screen.getAllByRole('button')
        
        // Should have: 1 Add Meal button + 2 Edit buttons + 2 Delete buttons = 5 total
        expect(allButtons.length).toBe(5)
      })
    })

    it('has correct meal data displayed', async () => {
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText('Test Meal 1')).toBeInTheDocument()
        expect(screen.getByText('Test Meal 2')).toBeInTheDocument()
        expect(screen.getByText('$15.99')).toBeInTheDocument()
        expect(screen.getByText('$12.99')).toBeInTheDocument()
      })
    })
  })

  describe('Image Upload', () => {
    it('handles image file selection', async () => {
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /add meal/i }))
      })
      
      const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      const input = screen.getByLabelText(/Click to upload meal image/)
      
      fireEvent.change(input, { target: { files: [file] } })
      
      expect(global.URL.createObjectURL).toHaveBeenCalledWith(file)
    })

    it('validates image file type', async () => {
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /add meal/i }))
      })
      
      const file = new File(['test'], 'test.txt', { type: 'text/plain' })
      const input = screen.getByLabelText(/Click to upload meal image/)
      
      fireEvent.change(input, { target: { files: [file] } })
      
      expect(global.URL.createObjectURL).not.toHaveBeenCalled()
    })

    it('validates image file size', async () => {
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /add meal/i }))
      })
      
      // Create a file larger than 5MB
      const largeFile = new File(['x'.repeat(6 * 1024 * 1024)], 'large.jpg', { type: 'image/jpeg' })
      const input = screen.getByLabelText(/Click to upload meal image/)
      
      fireEvent.change(input, { target: { files: [largeFile] } })
      
      expect(global.URL.createObjectURL).not.toHaveBeenCalled()
    })

    it('accepts valid image file types', () => {
      const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      expect(file.type).toBe('image/jpeg')
      expect(file.name).toBe('test.jpg')
    })
  })

  describe('Form Validation', () => {
    it('processes tags correctly', async () => {
      ;(api.createMeal as jest.Mock).mockResolvedValue({})
      
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /add meal/i }))
      })
      
      fireEvent.change(screen.getByLabelText(/Meal Name/), { target: { value: 'Test' } })
      fireEvent.change(screen.getByLabelText(/Base Price/), { target: { value: '10' } })
      fireEvent.change(screen.getByLabelText(/Quantity/), { target: { value: '5' } })
      fireEvent.change(screen.getByLabelText(/Tags/), { target: { value: 'vegan, healthy, organic' } })
      
      fireEvent.click(screen.getAllByText('Add Meal')[1])
      
      await waitFor(() => {
        expect(api.createMeal).toHaveBeenCalledWith(
          expect.objectContaining({
            tags: ['vegan', 'healthy', 'organic']
          })
        )
      })
    })

    it('processes allergens correctly', async () => {
      ;(api.createMeal as jest.Mock).mockResolvedValue({})
      
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /add meal/i }))
      })
      
      fireEvent.change(screen.getByLabelText(/Meal Name/), { target: { value: 'Test' } })
      fireEvent.change(screen.getByLabelText(/Base Price/), { target: { value: '10' } })
      fireEvent.change(screen.getByLabelText(/Quantity/), { target: { value: '5' } })
      fireEvent.change(screen.getByLabelText(/Allergens/), { target: { value: 'nuts, dairy' } })
      
      fireEvent.click(screen.getAllByText('Add Meal')[1])
      
      await waitFor(() => {
        expect(api.createMeal).toHaveBeenCalledWith(
          expect.objectContaining({
            allergens: ['nuts', 'dairy']
          })
        )
      })
    })
  })

  describe('Meal Display', () => {
    it('displays meal badges correctly', async () => {
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText('Out of Stock')).toBeInTheDocument()
      })
    })

    it('displays low stock badge', async () => {
      const lowStockMeals = [
        { ...mockMeals[0], quantity: 3 }
      ]
      ;(api.getOwnerMeals as jest.Mock).mockResolvedValue(lowStockMeals)
      
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText('Low Stock')).toBeInTheDocument()
      })
    })

    it('displays meal tags', async () => {
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText('vegetarian')).toBeInTheDocument()
        expect(screen.getByText('healthy')).toBeInTheDocument()
      })
    })

    it('displays meal allergens', async () => {
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText(/Allergens:/)).toBeInTheDocument()
        expect(screen.getByText(/gluten/)).toBeInTheDocument()
      })
    })
  })

  describe('Data Management', () => {
    it('calculates total stock correctly', async () => {
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText('10 items in stock')).toBeInTheDocument()
      })
    })

    it('displays meal statistics', async () => {
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText('Total Meals')).toBeInTheDocument()
        expect(screen.getByText('2')).toBeInTheDocument()
      })
    })

    it('shows meal tags when available', async () => {
      render(<OwnerDashboard />)
      
      await waitFor(() => {
        expect(screen.getByText('vegetarian')).toBeInTheDocument()
        expect(screen.getByText('healthy')).toBeInTheDocument()
        expect(screen.getByText('vegan')).toBeInTheDocument()
      })
    })
  })
})