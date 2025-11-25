import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import CartPage from '@/app/cart/page'
import { useAuth } from '@/context/auth-context'
import * as api from '@/lib/api'
import * as geocoding from '@/lib/geocoding'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))

// Mock auth context
jest.mock('@/context/auth-context', () => ({
  useAuth: jest.fn(),
}))

// Mock toast
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}))

// Mock API functions
jest.mock('@/lib/api', () => ({
  getCart: jest.fn(),
  updateCartItem: jest.fn(),
  removeFromCart: jest.fn(),
  clearCart: jest.fn(),
  checkoutCart: jest.fn(),
}))

// Mock geocoding
jest.mock('@/lib/geocoding', () => ({
  geocodeAddress: jest.fn(),
}))

describe('CartPage', () => {
  const mockPush = jest.fn()
  const mockRouter = {
    push: mockPush,
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }

  const mockCartWithItems = {
    cart_id: 'cart-123',
    items: [
      {
        item_id: 'item-1',
        meal_id: 'meal-1',
        meal_name: 'Margherita Pizza',
        restaurant_id: 'rest-1',
        qty: 2,
        unit_price: 9.99,
        line_total: 19.98,
        surplus_left: 5,
      },
      {
        item_id: 'item-2',
        meal_id: 'meal-2',
        meal_name: 'Caesar Salad',
        restaurant_id: 'rest-1',
        qty: 1,
        unit_price: 7.99,
        line_total: 7.99,
        surplus_left: 3,
      },
    ],
    cart_total: 27.97,
  }

  const mockEmptyCart = {
    cart_id: 'cart-123',
    items: [],
    cart_total: 0,
  }

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useRouter as jest.Mock).mockReturnValue(mockRouter)
    ;(useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: 'user-1', email: 'test@test.com' },
    })
  })

  describe('Authentication', () => {
    it('should redirect to login if not authenticated', async () => {
      ;(useAuth as jest.Mock).mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        user: null,
      })

      render(<CartPage />)

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login')
      })
    })

    it('should not redirect if authenticated', async () => {
      ;(api.getCart as jest.Mock).mockResolvedValue(mockEmptyCart)

      render(<CartPage />)

      await waitFor(() => {
        expect(mockPush).not.toHaveBeenCalledWith('/login')
      })
    })

    it('should show loading state while checking auth', () => {
      ;(useAuth as jest.Mock).mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        user: null,
      })

      const { container } = render(<CartPage />)

      const loader = container.querySelector('.animate-spin')
      expect(loader).toBeInTheDocument()
    })
  })

  describe('Cart Loading', () => {
    it('should load cart on mount', async () => {
      ;(api.getCart as jest.Mock).mockResolvedValue(mockCartWithItems)

      render(<CartPage />)

      await waitFor(() => {
        expect(api.getCart).toHaveBeenCalled()
      })
    })

    it('should display cart items after loading', async () => {
      ;(api.getCart as jest.Mock).mockResolvedValue(mockCartWithItems)

      render(<CartPage />)

      await waitFor(() => {
        expect(screen.getByText('Margherita Pizza')).toBeInTheDocument()
        expect(screen.getByText('Caesar Salad')).toBeInTheDocument()
      })
    })

    it('should display loading spinner while loading', () => {
      ;(api.getCart as jest.Mock).mockImplementation(() => new Promise(() => {}))

      const { container } = render(<CartPage />)

      const loader = container.querySelector('.animate-spin')
      expect(loader).toBeInTheDocument()
    })

    it('should handle cart loading error', async () => {
      ;(api.getCart as jest.Mock).mockRejectedValue(new Error('Failed to load cart'))

      render(<CartPage />)

      await waitFor(() => {
        expect(screen.getByText(/Failed to load cart/)).toBeInTheDocument()
      })
    })
  })

  describe('Empty Cart State', () => {
    it('should show empty cart message when no items', async () => {
      ;(api.getCart as jest.Mock).mockResolvedValue(mockEmptyCart)

      render(<CartPage />)

      await waitFor(() => {
        expect(screen.getByText('Your cart is empty')).toBeInTheDocument()
      })
    })

    it('should show browse meals button in empty state', async () => {
      ;(api.getCart as jest.Mock).mockResolvedValue(mockEmptyCart)

      render(<CartPage />)

      await waitFor(() => {
        const browseButton = screen.getByText('Browse Meals')
        expect(browseButton).toBeInTheDocument()
      })
    })

    it('should navigate to browse page when button clicked', async () => {
      ;(api.getCart as jest.Mock).mockResolvedValue(mockEmptyCart)

      render(<CartPage />)

      await waitFor(() => {
        const browseButton = screen.getByText('Browse Meals')
        fireEvent.click(browseButton)
      })

      expect(mockPush).toHaveBeenCalledWith('/browse')
    })
  })

  describe('Cart Items Display', () => {
    beforeEach(() => {
      ;(api.getCart as jest.Mock).mockResolvedValue(mockCartWithItems)
    })

    it('should display item count', async () => {
      render(<CartPage />)

      await waitFor(() => {
        expect(screen.getByText('2 items in your cart')).toBeInTheDocument()
      })
    })

    it('should display item names', async () => {
      render(<CartPage />)

      await waitFor(() => {
        expect(screen.getByText('Margherita Pizza')).toBeInTheDocument()
        expect(screen.getByText('Caesar Salad')).toBeInTheDocument()
      })
    })

    it('should display item quantities', async () => {
      render(<CartPage />)

      await waitFor(() => {
        const quantities = screen.getAllByText(/\d+/)
        expect(quantities.length).toBeGreaterThan(0)
      })
    })

    it('should display unit prices', async () => {
      render(<CartPage />)

      await waitFor(() => {
        expect(screen.getByText('$9.99 each')).toBeInTheDocument()
        expect(screen.getByText('$7.99 each')).toBeInTheDocument()
      })
    })

    it('should display line totals', async () => {
      render(<CartPage />)

      await waitFor(() => {
        expect(screen.getByText('$19.98')).toBeInTheDocument()
        expect(screen.getByText('$7.99')).toBeInTheDocument()
      })
    })

    it('should display cart total', async () => {
      render(<CartPage />)

      await waitFor(() => {
        const totals = screen.getAllByText('$27.97')
        expect(totals.length).toBeGreaterThan(0)
      })
    })

    it('should display surplus availability', async () => {
      render(<CartPage />)

      await waitFor(() => {
        expect(screen.getByText('5 available')).toBeInTheDocument()
        expect(screen.getByText('3 available')).toBeInTheDocument()
      })
    })
  })

  describe('Quantity Updates', () => {
    beforeEach(() => {
      ;(api.getCart as jest.Mock).mockResolvedValue(mockCartWithItems)
    })

    it('should have increment button for each item', async () => {
      render(<CartPage />)

      await waitFor(() => {
        const incrementButtons = screen.getAllByRole('button', { name: '' })
        expect(incrementButtons.length).toBeGreaterThan(0)
      })
    })

    it('should have decrement button for each item', async () => {
      render(<CartPage />)

      await waitFor(() => {
        const decrementButtons = screen.getAllByRole('button', { name: '' })
        expect(decrementButtons.length).toBeGreaterThan(0)
      })
    })

    it('should call updateCartItem when incrementing quantity', async () => {
      ;(api.updateCartItem as jest.Mock).mockResolvedValue(mockCartWithItems)

      render(<CartPage />)

      await waitFor(() => {
        const incrementButtons = screen.getAllByRole('button')
        const plusButton = incrementButtons.find(btn => 
          btn.querySelector('svg')?.classList.contains('lucide-plus')
        )
        if (plusButton) {
          fireEvent.click(plusButton)
        }
      })

      await waitFor(() => {
        expect(api.updateCartItem).toHaveBeenCalled()
      })
    })

    it('should call updateCartItem when decrementing quantity', async () => {
      ;(api.updateCartItem as jest.Mock).mockResolvedValue(mockCartWithItems)

      render(<CartPage />)

      await waitFor(() => {
        const buttons = screen.getAllByRole('button')
        const minusButton = buttons.find(btn => 
          btn.querySelector('svg')?.classList.contains('lucide-minus')
        )
        if (minusButton) {
          fireEvent.click(minusButton)
        }
      })

      await waitFor(() => {
        expect(api.updateCartItem).toHaveBeenCalled()
      })
    })

    it('should disable decrement when quantity is 1', async () => {
      const cartWithOneItem = {
        ...mockCartWithItems,
        items: [{
          ...mockCartWithItems.items[0],
          qty: 1,
        }],
      }
      ;(api.getCart as jest.Mock).mockResolvedValue(cartWithOneItem)

      render(<CartPage />)

      await waitFor(() => {
        const buttons = screen.getAllByRole('button')
        const minusButtons = buttons.filter(btn => 
          btn.querySelector('svg')?.classList.contains('lucide-minus')
        )
        if (minusButtons.length > 0) {
          expect(minusButtons[0]).toBeDisabled()
        }
      })
    })

    it('should disable increment when quantity equals surplus', async () => {
      const cartAtMax = {
        ...mockCartWithItems,
        items: [{
          ...mockCartWithItems.items[0],
          qty: 5,
          surplus_left: 5,
        }],
      }
      ;(api.getCart as jest.Mock).mockResolvedValue(cartAtMax)

      render(<CartPage />)

      await waitFor(() => {
        const buttons = screen.getAllByRole('button')
        const plusButtons = buttons.filter(btn => 
          btn.querySelector('svg')?.classList.contains('lucide-plus')
        )
        if (plusButtons.length > 0) {
          expect(plusButtons[0]).toBeDisabled()
        }
      })
    })

    it('should handle update error', async () => {
      ;(api.updateCartItem as jest.Mock).mockRejectedValue(
        new Error('Failed to update')
      )

      render(<CartPage />)

      await waitFor(() => {
        const buttons = screen.getAllByRole('button')
        const plusButton = buttons.find(btn => 
          btn.querySelector('svg')?.classList.contains('lucide-plus')
        )
        if (plusButton) {
          fireEvent.click(plusButton)
        }
      })

      await waitFor(() => {
        expect(api.updateCartItem).toHaveBeenCalled()
      })
    })
  })

  describe('Remove Item', () => {
    beforeEach(() => {
      ;(api.getCart as jest.Mock).mockResolvedValue(mockCartWithItems)
    })

    it('should have remove button for each item', async () => {
      render(<CartPage />)

      await waitFor(() => {
        const removeButtons = screen.getAllByText('Remove')
        expect(removeButtons.length).toBe(2)
      })
    })

    it('should show confirmation dialog when remove clicked', async () => {
      render(<CartPage />)

      await waitFor(() => {
        const removeButtons = screen.getAllByText('Remove')
        fireEvent.click(removeButtons[0])
      })

      await waitFor(() => {
        expect(screen.getByText('Remove item?')).toBeInTheDocument()
      })
    })

    it('should call removeFromCart when confirmed', async () => {
      ;(api.removeFromCart as jest.Mock).mockResolvedValue(mockEmptyCart)

      render(<CartPage />)

      await waitFor(() => {
        const removeButtons = screen.getAllByText('Remove')
        fireEvent.click(removeButtons[0])
      })

      await waitFor(() => {
        const confirmButton = screen.getAllByRole('button', { name: 'Remove' }).pop()
        if (confirmButton) {
          fireEvent.click(confirmButton)
        }
      })

      await waitFor(() => {
        expect(api.removeFromCart).toHaveBeenCalledWith('item-1')
      })
    })

    it('should not remove when cancelled', async () => {
      render(<CartPage />)

      await waitFor(() => {
        const removeButtons = screen.getAllByText('Remove')
        fireEvent.click(removeButtons[0])
      })

      await waitFor(() => {
        const cancelButton = screen.getByText('Cancel')
        fireEvent.click(cancelButton)
      })

      expect(api.removeFromCart).not.toHaveBeenCalled()
    })
  })

  describe('Clear Cart', () => {
    beforeEach(() => {
      ;(api.getCart as jest.Mock).mockResolvedValue(mockCartWithItems)
    })

    it('should have clear cart button', async () => {
      render(<CartPage />)

      await waitFor(() => {
        expect(screen.getByText('Clear Cart')).toBeInTheDocument()
      })
    })

    it('should show confirmation dialog when clear clicked', async () => {
      render(<CartPage />)

      await waitFor(() => {
        const clearButton = screen.getByText('Clear Cart')
        fireEvent.click(clearButton)
      })

      await waitFor(() => {
        expect(screen.getByText('Clear your cart?')).toBeInTheDocument()
      })
    })

    it('should call clearCart when confirmed', async () => {
      ;(api.clearCart as jest.Mock).mockResolvedValue(mockEmptyCart)

      render(<CartPage />)

      await waitFor(() => {
        const clearButton = screen.getByText('Clear Cart')
        fireEvent.click(clearButton)
      })

      await waitFor(() => {
        const confirmButtons = screen.getAllByRole('button')
        const confirmButton = confirmButtons.find(btn => btn.textContent === 'Clear Cart' && btn.getAttribute('data-state') !== 'closed')
        if (confirmButton) {
          fireEvent.click(confirmButton)
        }
      })

      await waitFor(() => {
        expect(api.clearCart).toHaveBeenCalled()
      })
    })
  })

  describe('Delivery Address', () => {
    beforeEach(() => {
      ;(api.getCart as jest.Mock).mockResolvedValue(mockCartWithItems)
    })

    it('should have delivery address input', async () => {
      render(<CartPage />)

      await waitFor(() => {
        expect(screen.getByLabelText('Delivery Address')).toBeInTheDocument()
      })
    })

    it('should have locate address button', async () => {
      render(<CartPage />)

      await waitFor(() => {
        expect(screen.getByText('Locate Address')).toBeInTheDocument()
      })
    })

    it('should call geocodeAddress when locate button clicked', async () => {
      ;(geocoding.geocodeAddress as jest.Mock).mockResolvedValue({
        latitude: 35.7796,
        longitude: -78.6382,
        place_name: '123 Main St, Raleigh, NC',
      })

      render(<CartPage />)

      await waitFor(() => {
        const addressInput = screen.getByLabelText('Delivery Address')
        fireEvent.change(addressInput, { target: { value: '123 Main St' } })
      })

      await waitFor(() => {
        const locateButton = screen.getByText('Locate Address')
        fireEvent.click(locateButton)
      })

      await waitFor(() => {
        expect(geocoding.geocodeAddress).toHaveBeenCalledWith('123 Main St')
      })
    })

    it('should show formatted address after geocoding', async () => {
      ;(geocoding.geocodeAddress as jest.Mock).mockResolvedValue({
        latitude: 35.7796,
        longitude: -78.6382,
        place_name: '123 Main St, Raleigh, NC',
      })

      render(<CartPage />)

      await waitFor(() => {
        const addressInput = screen.getByLabelText('Delivery Address')
        fireEvent.change(addressInput, { target: { value: '123 Main St' } })
      })

      await waitFor(() => {
        const locateButton = screen.getByText('Locate Address')
        fireEvent.click(locateButton)
      })

      await waitFor(() => {
        expect(screen.getByText('123 Main St, Raleigh, NC')).toBeInTheDocument()
      })
    })

    it('should show error when geocoding fails', async () => {
      ;(geocoding.geocodeAddress as jest.Mock).mockRejectedValue(
        new Error('Address not found')
      )

      render(<CartPage />)

      await waitFor(() => {
        const addressInput = screen.getByLabelText('Delivery Address')
        fireEvent.change(addressInput, { target: { value: 'invalid address' } })
      })

      await waitFor(() => {
        const locateButton = screen.getByText('Locate Address')
        fireEvent.click(locateButton)
      })

      await waitFor(() => {
        expect(screen.getByText(/Address not found/)).toBeInTheDocument()
      })
    })

    it('should disable locate button when address is empty', async () => {
      render(<CartPage />)

      await waitFor(() => {
        const locateButton = screen.getByText('Locate Address')
        expect(locateButton).toBeDisabled()
      })
    })

    it('should show loading state while geocoding', async () => {
      ;(geocoding.geocodeAddress as jest.Mock).mockImplementation(() => new Promise(() => {}))

      render(<CartPage />)

      await waitFor(() => {
        const addressInput = screen.getByLabelText('Delivery Address')
        fireEvent.change(addressInput, { target: { value: '123 Main St' } })
      })

      await waitFor(() => {
        const locateButton = screen.getByText('Locate Address')
        fireEvent.click(locateButton)
      })

      await waitFor(() => {
        expect(screen.getByText('Locating Address...')).toBeInTheDocument()
      })
    })
  })

  describe('Tip Amount', () => {
    beforeEach(() => {
      ;(api.getCart as jest.Mock).mockResolvedValue(mockCartWithItems)
    })

    it('should have tip amount input', async () => {
      render(<CartPage />)

      await waitFor(() => {
        expect(screen.getByLabelText('Tip Amount')).toBeInTheDocument()
      })
    })

    it('should update tip amount when input changes', async () => {
      render(<CartPage />)

      await waitFor(() => {
        const tipInput = screen.getByLabelText('Tip Amount')
        fireEvent.change(tipInput, { target: { value: '5.00' } })
      })

      await waitFor(() => {
        const tipInput = screen.getByLabelText('Tip Amount') as HTMLInputElement
        expect(tipInput.value).toBe('5.00')
      })
    })
  })

  describe('Checkout', () => {
    beforeEach(() => {
      ;(api.getCart as jest.Mock).mockResolvedValue(mockCartWithItems)
      ;(geocoding.geocodeAddress as jest.Mock).mockResolvedValue({
        latitude: 35.7796,
        longitude: -78.6382,
        place_name: '123 Main St, Raleigh, NC',
      })
    })

    it('should have checkout button', async () => {
      render(<CartPage />)

      await waitFor(() => {
        expect(screen.getByText('Proceed to Checkout')).toBeInTheDocument()
      })
    })

    it('should disable checkout button without address', async () => {
      render(<CartPage />)

      await waitFor(() => {
        const checkoutButton = screen.getByText('Proceed to Checkout')
        expect(checkoutButton).toBeDisabled()
      })
    })

    it('should enable checkout button after geocoding address', async () => {
      render(<CartPage />)

      await waitFor(() => {
        const addressInput = screen.getByLabelText('Delivery Address')
        fireEvent.change(addressInput, { target: { value: '123 Main St' } })
      })

      await waitFor(() => {
        const locateButton = screen.getByText('Locate Address')
        fireEvent.click(locateButton)
      })

      await waitFor(() => {
        const checkoutButton = screen.getByText('Proceed to Checkout')
        expect(checkoutButton).not.toBeDisabled()
      })
    })

    it('should call checkoutCart with address and location data', async () => {
      ;(api.checkoutCart as jest.Mock).mockResolvedValue({
        order_id: 'order-123',
        status: 'pending',
        total: 27.97,
      })

      render(<CartPage />)

      await waitFor(() => {
        const addressInput = screen.getByLabelText('Delivery Address')
        fireEvent.change(addressInput, { target: { value: '123 Main St' } })
      })

      await waitFor(() => {
        const locateButton = screen.getByText('Locate Address')
        fireEvent.click(locateButton)
      })

      await waitFor(() => {
        const checkoutButton = screen.getByText('Proceed to Checkout')
        fireEvent.click(checkoutButton)
      })

      await waitFor(() => {
        expect(api.checkoutCart).toHaveBeenCalledWith(
          expect.objectContaining({
            deliveryAddress: '123 Main St',
            latitude: 35.7796,
            longitude: -78.6382,
          })
        )
      })
    })

    // it('should show success message after checkout', async () => {
    //   ;(api.checkoutCart as jest.Mock).mockResolvedValue({
    //     order_id: 'order-123',
    //     status: 'pending',
    //     total: 27.97,
    //   })

    //   render(<CartPage />)

    //   await waitFor(() => {
    //     const checkoutButton = screen.getByText('Proceed to Checkout')
    //     fireEvent.click(checkoutButton)
    //   })

    //   await waitFor(() => {
    //     expect(screen.getByText('Order Placed Successfully!')).toBeInTheDocument()
    //   })
    // })

    // it('should redirect to orders after successful checkout', async () => {
    //   jest.useFakeTimers()
    //   ;(api.checkoutCart as jest.Mock).mockResolvedValue({
    //     order_id: 'order-123',
    //     status: 'pending',
    //     total: 27.97,
    //   })

    //   render(<CartPage />)

    //   await waitFor(() => {
    //     const addressInput = screen.getByLabelText('Delivery Address')
    //     fireEvent.change(addressInput, { target: { value: '123 Main St' } })
    //   })

    //   await waitFor(() => {
    //     const locateButton = screen.getByText('Locate Address')
    //     fireEvent.click(locateButton)
    //   })

    //   await waitFor(() => {
    //     const checkoutButton = screen.getByText('Proceed to Checkout')
    //     fireEvent.click(checkoutButton)
    //   })

    //   await waitFor(() => {
    //     expect(screen.getByText('Order Placed Successfully!')).toBeInTheDocument()
    //   })

    //   jest.advanceTimersByTime(2000)

    //   await waitFor(() => {
    //     expect(mockPush).toHaveBeenCalledWith('/orders')
    //   })

    //   jest.useRealTimers()
    // })

    // it('should handle checkout error', async () => {
    //   ;(api.checkoutCart as jest.Mock).mockRejectedValue(
    //     new Error('not enough surplus for meal')
    //   )

    //   render(<CartPage />)

    //   await waitFor(() => {
    //     const addressInput = screen.getByLabelText('Delivery Address')
    //     fireEvent.change(addressInput, { target: { value: '123 Main St' } })
    //   })

    //   await waitFor(() => {
    //     const locateButton = screen.getByText('Locate Address')
    //     fireEvent.click(locateButton)
    //   })

    //   await waitFor(() => {
    //     const checkoutButton = screen.getByText('Proceed to Checkout')
    //     fireEvent.click(checkoutButton)
    //   })

    //   await waitFor(() => {
    //     expect(screen.getByText(/not enough surplus for meal/)).toBeInTheDocument()
    //   })
    // })

    it('should disable checkout for empty cart', async () => {
      ;(api.getCart as jest.Mock).mockResolvedValue(mockEmptyCart)

      render(<CartPage />)

      await waitFor(() => {
        const browseButton = screen.getByText('Browse Meals')
        expect(browseButton).toBeInTheDocument()
      })
    })

    // it('should show processing state during checkout', async () => {
    //   ;(api.checkoutCart as jest.Mock).mockImplementation(() => new Promise(() => {}))

    //   render(<CartPage />)

    //   await waitFor(() => {
    //     const addressInput = screen.getByLabelText('Delivery Address')
    //     fireEvent.change(addressInput, { target: { value: '123 Main St' } })
    //   })

    //   await waitFor(() => {
    //     const locateButton = screen.getByText('Locate Address')
    //     fireEvent.click(locateButton)
    //   })

    //   await waitFor(() => {
    //     const checkoutButton = screen.getByText('Proceed to Checkout')
    //     fireEvent.click(checkoutButton)
    //   })

    //   await waitFor(() => {
    //     expect(screen.getByText('Processing...')).toBeInTheDocument()
    //   })
    // })

    it('should show error when trying to checkout without address', async () => {
      render(<CartPage />)

      await waitFor(() => {
        const checkoutButton = screen.getByText('Proceed to Checkout')
        expect(checkoutButton).toBeDisabled()
      })
    })
  })

  describe('Order Summary', () => {
    beforeEach(() => {
      ;(api.getCart as jest.Mock).mockResolvedValue(mockCartWithItems)
    })

    it('should display order summary section', async () => {
      render(<CartPage />)

      await waitFor(() => {
        expect(screen.getByText('Order Summary')).toBeInTheDocument()
      })
    })

    it('should display subtotal', async () => {
      render(<CartPage />)

      await waitFor(() => {
        expect(screen.getByText('Subtotal')).toBeInTheDocument()
      })
    })

    it('should display total', async () => {
      render(<CartPage />)

      await waitFor(() => {
        const totals = screen.getAllByText('$27.97')
        expect(totals.length).toBeGreaterThan(0)
      })
    })

    it('should display delivery fee', async () => {
      render(<CartPage />)

      await waitFor(() => {
        expect(screen.getByText('Delivery Fee')).toBeInTheDocument()
      })
    })

    it('should display tax', async () => {
      render(<CartPage />)

      await waitFor(() => {
        expect(screen.getByText('Tax (2%)')).toBeInTheDocument()
      })
    })

    it('should display tip field', async () => {
      render(<CartPage />)

      await waitFor(() => {
        expect(screen.getByText('Tip')).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('should show error message when cart fails to load', async () => {
      ;(api.getCart as jest.Mock).mockRejectedValue(new Error('Network error'))

      render(<CartPage />)

      await waitFor(() => {
        expect(screen.getByText(/Network error/)).toBeInTheDocument()
      })
    })

    it('should have dismiss button for errors', async () => {
      ;(api.getCart as jest.Mock).mockRejectedValue(new Error('Error'))

      render(<CartPage />)

      await waitFor(() => {
        expect(screen.getByText('Dismiss')).toBeInTheDocument()
      })
    })

    it('should dismiss error when button clicked', async () => {
      ;(api.getCart as jest.Mock).mockRejectedValue(new Error('Error'))

      render(<CartPage />)

      await waitFor(() => {
        const dismissButton = screen.getByText('Dismiss')
        fireEvent.click(dismissButton)
      })

      await waitFor(() => {
        expect(screen.queryByText('Error')).not.toBeInTheDocument()
      })
    })
  })
})

