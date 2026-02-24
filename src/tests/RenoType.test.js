import { render, screen, fireEvent, act } from '@testing-library/react'
import React from "react"
import RenoType from "../components/RenoType"

const mockOnNext = jest.fn()
const mockOnBack = jest.fn()

// Reset mocks before each test
beforeEach(() => {
  jest.clearAllMocks()
  jest.useFakeTimers()
})

afterEach(() => {
  jest.runOnlyPendingTimers()
  jest.useRealTimers()
})

// ============================================================
// SECTION 1: Basic Rendering Tests
// Verifies the component mounts and all core UI elements are present
// ============================================================

test('renders the heading', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  expect(screen.getByText(/What would you like to renovate\?/i)).toBeInTheDocument()
})

test('renders the Next button', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  expect(screen.getByRole('button', { name: /Next/i })).toBeInTheDocument()
})

test('renders the Back button', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  expect(screen.getByRole('button', { name: /Back/i })).toBeInTheDocument()
})

test('renders all 6 renovation options', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  expect(screen.getByText(/Full renovation/i)).toBeInTheDocument()
  expect(screen.getByText(/^Bedroom$/i)).toBeInTheDocument()
  expect(screen.getByText(/^Kitchen$/i)).toBeInTheDocument()
  expect(screen.getByText(/^Bathroom$/i)).toBeInTheDocument()
  expect(screen.getByText(/^Living room$/i)).toBeInTheDocument()
  expect(screen.getByText(/Other\/Custom/i)).toBeInTheDocument()
})

// ============================================================
// SECTION 2: Initial State / Validation Tests
// Next is always clickable — shows error if nothing selected
// ============================================================

test('Next button is never disabled', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  expect(screen.getByRole('button', { name: /Next/i })).not.toBeDisabled()
})

test('onNext is NOT called when nothing is selected', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(mockOnNext).not.toHaveBeenCalled()
})

test('shows error message when Next is clicked with nothing selected', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(screen.getByText(/please select at least one option/i)).toBeInTheDocument()
})

test('error message does not show before Next is clicked', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  expect(screen.queryByText(/please select at least one option/i)).not.toBeInTheDocument()
})

test('error message disappears as soon as an option is selected', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  // Trigger error
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(screen.getByText(/please select at least one option/i)).toBeInTheDocument()

  // Select an option — error clears immediately without needing to click Next
  fireEvent.click(screen.getByText(/^Kitchen$/i))
  expect(screen.queryByText(/please select at least one option/i)).not.toBeInTheDocument()
})

// ============================================================
// SECTION 3: Single Selection Tests
// Verifies individual options can be selected
// ============================================================

test('clicking Kitchen selects it', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByText(/^Kitchen$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({ renovation_type: ['Kitchen'] })
})

test('clicking Bedroom selects it', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByText(/^Bedroom$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({ renovation_type: ['Bedroom'] })
})

test('clicking Bathroom selects it', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByText(/^Bathroom$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({ renovation_type: ['Bathroom'] })
})

test('clicking Living room selects it', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByText(/^Living room$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({ renovation_type: ['Living room'] })
})

test('clicking Other/Custom selects it', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByText(/Other\/Custom/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({ renovation_type: ['Other/Custom'] })
})

// ============================================================
// SECTION 4: Multi-Selection Tests
// Verifies multiple options can be selected together
// ============================================================

test('can select multiple options together', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByText(/^Kitchen$/i))
  fireEvent.click(screen.getByText(/^Bedroom$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({
    renovation_type: expect.arrayContaining(['Kitchen', 'Bedroom'])
  })
})

test('can select 3 options at once', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByText(/^Kitchen$/i))
  fireEvent.click(screen.getByText(/^Bedroom$/i))
  fireEvent.click(screen.getByText(/^Bathroom$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({
    renovation_type: expect.arrayContaining(['Kitchen', 'Bedroom', 'Bathroom'])
  })
  expect(mockOnNext.mock.calls[0][0].renovation_type).toHaveLength(3)
})

test('onNext is called exactly once when Next is clicked with valid selection', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByText(/^Kitchen$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledTimes(1)
})

// ============================================================
// SECTION 5: Deselection (Toggle) Tests
// Verifies options can be toggled off by clicking again
// ============================================================

test('clicking a selected option deselects it', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  // Select then deselect Kitchen
  fireEvent.click(screen.getByText(/^Kitchen$/i))
  fireEvent.click(screen.getByText(/^Kitchen$/i))

  // onNext should not be called since nothing is selected
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(mockOnNext).not.toHaveBeenCalled()
})

test('deselecting an option removes it from the payload', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByText(/^Kitchen$/i))
  fireEvent.click(screen.getByText(/^Bedroom$/i))

  // Deselect Kitchen
  fireEvent.click(screen.getByText(/^Kitchen$/i))

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({ renovation_type: ['Bedroom'] })
})

test('deselecting all options means onNext is not called on Next click', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByText(/^Kitchen$/i))
  fireEvent.click(screen.getByText(/^Kitchen$/i))

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(mockOnNext).not.toHaveBeenCalled()
})

// ============================================================
// SECTION 6: Full Renovation Special Logic Tests
// Full renovation overrides all other selections
// ============================================================

test('selecting Full renovation deselects all other options', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  // Select some options first
  fireEvent.click(screen.getByText(/^Kitchen$/i))
  fireEvent.click(screen.getByText(/^Bedroom$/i))

  // Now select Full renovation
  fireEvent.click(screen.getByText(/^Full renovation$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  // Should only contain Full renovation
  expect(mockOnNext).toHaveBeenCalledWith({ renovation_type: ['Full renovation'] })
  expect(mockOnNext.mock.calls[0][0].renovation_type).toHaveLength(1)
})

test('selecting another option after Full renovation removes Full renovation', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByText(/^Full renovation$/i))
  fireEvent.click(screen.getByText(/^Kitchen$/i))

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  const result = mockOnNext.mock.calls[0][0].renovation_type
  expect(result).not.toContain('Full renovation')
  expect(result).toContain('Kitchen')
})

test('Full renovation on its own calls onNext with only Full renovation', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByText(/^Full renovation$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({ renovation_type: ['Full renovation'] })
})

// ============================================================
// SECTION 7: Auto-switch to Full Renovation Tests
// Selecting 4 non-full options triggers a delayed switch to Full renovation
// ============================================================

test('selecting 4 options triggers delayed switch to Full renovation', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByText(/^Kitchen$/i))
  fireEvent.click(screen.getByText(/^Bedroom$/i))
  fireEvent.click(screen.getByText(/^Bathroom$/i))
  fireEvent.click(screen.getByText(/^Living room$/i))

  // After the timeout, should switch to Full renovation
  act(() => { jest.runAllTimers() })

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(mockOnNext).toHaveBeenCalledWith({ renovation_type: ['Full renovation'] })
})

test('all 4 options are briefly visible before switching to Full renovation', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByText(/^Kitchen$/i))
  fireEvent.click(screen.getByText(/^Bedroom$/i))
  fireEvent.click(screen.getByText(/^Bathroom$/i))
  fireEvent.click(screen.getByText(/^Living room$/i))

  // Before timer fires, all 4 should still be selected (Next is enabled)
  expect(screen.getByRole('button', { name: /Next/i })).not.toBeDisabled()

  act(() => { jest.runAllTimers() })
})

test('selecting only 3 options does NOT trigger auto-switch to Full renovation', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByText(/^Kitchen$/i))
  fireEvent.click(screen.getByText(/^Bedroom$/i))
  fireEvent.click(screen.getByText(/^Bathroom$/i))

  act(() => { jest.runAllTimers() })

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  const result = mockOnNext.mock.calls[0][0].renovation_type
  expect(result).not.toContain('Full renovation')
  expect(result).toHaveLength(3)
})

// ============================================================
// SECTION 8: Callback Tests
// Verifies onNext and onBack are called correctly
// ============================================================

test('calls onBack when Back button is clicked', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByRole('button', { name: /Back/i }))

  expect(mockOnBack).toHaveBeenCalledTimes(1)
})

test('onNext is NOT called when Back is clicked', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByRole('button', { name: /Back/i }))

  expect(mockOnNext).not.toHaveBeenCalled()
})

test('onBack is NOT called when Next is clicked', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByText(/^Kitchen$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnBack).not.toHaveBeenCalled()
})

test('onNext passes renovation_type as an array', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByText(/^Kitchen$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  const arg = mockOnNext.mock.calls[0][0]
  expect(Array.isArray(arg.renovation_type)).toBe(true)
})

// ============================================================
// SECTION 9: Boundary / Edge Case Tests
// ============================================================

test('selecting and deselecting Full renovation re-enables other options', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  // Select Full renovation then deselect it
  fireEvent.click(screen.getByText(/^Full renovation$/i))
  fireEvent.click(screen.getByText(/^Full renovation$/i))

  // Now select Kitchen — should work normally
  fireEvent.click(screen.getByText(/^Kitchen$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({ renovation_type: ['Kitchen'] })
})

test('onNext is NOT called when Full renovation was selected then deselected', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByText(/^Full renovation$/i))
  fireEvent.click(screen.getByText(/^Full renovation$/i))

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(mockOnNext).not.toHaveBeenCalled()
})

test('clicking Next multiple times with valid selection only calls onNext each time', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByText(/^Kitchen$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledTimes(2)
})

test('renovation_type array contains the correct number of items when 2 selected', () => {
  render(<RenoType onNext={mockOnNext} onBack={mockOnBack} />)

  fireEvent.click(screen.getByText(/^Kitchen$/i))
  fireEvent.click(screen.getByText(/^Living room$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext.mock.calls[0][0].renovation_type).toHaveLength(2)
})