import { render, screen, fireEvent } from '@testing-library/react'
import React from "react"
import SqftToReno from "../components/SqftToReno"

const mockOnNext = jest.fn()
const mockOnBack = jest.fn()

// Reset mocks before each test
beforeEach(() => {
  jest.clearAllMocks()
})

// ============================================================
// SECTION 1: Basic Rendering Tests
// Verifies the component mounts and core UI elements are present
// ============================================================

test('renders the heading', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Sqft to Renovate/i)).toBeInTheDocument()
})

test('renders the Next button', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByRole('button', { name: /Next/i })).toBeInTheDocument()
})

test('renders the Back button', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByRole('button', { name: /Back/i })).toBeInTheDocument()
})

test('renders an input for a single other renovation type', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/^Kitchen$/i)).toBeInTheDocument()
  expect(screen.getByRole('textbox')).toBeInTheDocument()
})

test('renders the correct placeholder text on inputs', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByPlaceholderText(/Enter sqft to renovate/i)).toBeInTheDocument()
})

// ============================================================
// SECTION 2: Bedroom Input Rendering Tests
// Verifies bedroom inputs render based on bedrooms_to_reno count
// ============================================================

test('renders the correct number of bedroom inputs', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 2,
    bathrooms_to_reno: 0
  }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Bedroom 1/i)).toBeInTheDocument()
  expect(screen.getByText(/Bedroom 2/i)).toBeInTheDocument()
})

test('renders only 1 bedroom input when bedrooms_to_reno is 1', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 0
  }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Bedroom 1/i)).toBeInTheDocument()
  expect(screen.queryByText(/Bedroom 2/i)).not.toBeInTheDocument()
})

test('renders 3 bedroom inputs when bedrooms_to_reno is 3', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 3,
    bathrooms_to_reno: 0
  }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Bedroom 1/i)).toBeInTheDocument()
  expect(screen.getByText(/Bedroom 2/i)).toBeInTheDocument()
  expect(screen.getByText(/Bedroom 3/i)).toBeInTheDocument()
})

// ============================================================
// SECTION 3: Bathroom Input Rendering Tests
// ============================================================

test('renders the correct number of bathroom inputs', () => {
  const answers = {
    renovation_type: ['Bathroom'],
    bedrooms_to_reno: 0,
    bathrooms_to_reno: 2
  }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Bathroom 1/i)).toBeInTheDocument()
  expect(screen.getByText(/Bathroom 2/i)).toBeInTheDocument()
})

test('renders only 1 bathroom input when bathrooms_to_reno is 1', () => {
  const answers = {
    renovation_type: ['Bathroom'],
    bedrooms_to_reno: 0,
    bathrooms_to_reno: 1
  }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Bathroom 1/i)).toBeInTheDocument()
  expect(screen.queryByText(/Bathroom 2/i)).not.toBeInTheDocument()
})

// ============================================================
// SECTION 4: Mixed Renovation Type Rendering Tests
// ============================================================

test('renders bedroom, bathroom and other inputs when all selected', () => {
  const answers = {
    renovation_type: ['Bedroom', 'Bathroom', 'Kitchen'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 1
  }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Bedroom 1/i)).toBeInTheDocument()
  expect(screen.getByText(/Bathroom 1/i)).toBeInTheDocument()
  expect(screen.getByText(/^Kitchen$/i)).toBeInTheDocument()
})

test('renders two other renovation type inputs', () => {
  const answers = { renovation_type: ['Kitchen', 'Living room'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/^Kitchen$/i)).toBeInTheDocument()
  expect(screen.getByText(/^Living room$/i)).toBeInTheDocument()
})

// ============================================================
// SECTION 5: Full Renovation Tests
// Full renovation should show only one input and suppress others
// ============================================================

test('renders only one input for Full renovation', () => {
  const answers = { renovation_type: ['Full renovation'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/^Full renovation$/i)).toBeInTheDocument()
  expect(screen.getAllByRole('textbox')).toHaveLength(1)
})

test('does not render bedroom inputs when Full renovation is selected', () => {
  const answers = {
    renovation_type: ['Full renovation'],
    bedrooms_to_reno: 2,
    bathrooms_to_reno: 2
  }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.queryByText(/Bedroom 1/i)).not.toBeInTheDocument()
  expect(screen.queryByText(/Bathroom 1/i)).not.toBeInTheDocument()
})

test('does not render other reno type inputs when Full renovation is selected', () => {
  const answers = {
    renovation_type: ['Full renovation'],
    bedrooms_to_reno: 0,
    bathrooms_to_reno: 0
  }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.queryByText(/^Kitchen$/i)).not.toBeInTheDocument()
  expect(screen.getByText(/^Full renovation$/i)).toBeInTheDocument()
})

// ============================================================
// SECTION 6: Default Value Tests
// All inputs should start empty
// ============================================================

test('input defaults to empty string for other type', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByRole('textbox').value).toBe('')
})

test('bedroom input defaults to empty string', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 0
  }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByRole('textbox').value).toBe('')
})

test('Full renovation input defaults to empty string', () => {
  const answers = { renovation_type: ['Full renovation'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByRole('textbox').value).toBe('')
})

// ============================================================
// SECTION 7: Input Validation Tests
// Only whole numbers allowed — letters, decimals, special chars rejected
// ============================================================

test('accepts a valid number input', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const input = screen.getByRole('textbox')
  fireEvent.change(input, { target: { value: '150' } })

  expect(input.value).toBe('150')
})

test('accepts 0 as a valid input', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const input = screen.getByRole('textbox')
  fireEvent.change(input, { target: { value: '0' } })

  expect(input.value).toBe('0')
})

test('rejects letters — input stays empty', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const input = screen.getByRole('textbox')
  fireEvent.change(input, { target: { value: 'abc' } })

  expect(input.value).toBe('')
})

test('rejects decimal numbers', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const input = screen.getByRole('textbox')
  fireEvent.change(input, { target: { value: '12.5' } })

  expect(input.value).toBe('')
})

test('rejects special characters', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const input = screen.getByRole('textbox')
  fireEvent.change(input, { target: { value: '100!' } })

  expect(input.value).toBe('')
})

test('rejects negative numbers', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const input = screen.getByRole('textbox')
  fireEvent.change(input, { target: { value: '-50' } })

  expect(input.value).toBe('')
})

test('multiple inputs update independently', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 2,
    bathrooms_to_reno: 0
  }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const inputs = screen.getAllByRole('textbox')
  fireEvent.change(inputs[0], { target: { value: '100' } })
  fireEvent.change(inputs[1], { target: { value: '200' } })

  expect(inputs[0].value).toBe('100')
  expect(inputs[1].value).toBe('200')
})

// ============================================================
// SECTION 8: Validation / Error Message Tests
// Next button is always clickable — shows error if inputs are empty
// ============================================================

test('Next button is never disabled', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByRole('button', { name: /Next/i })).not.toBeDisabled()
})

test('onNext is NOT called when input is empty', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).not.toHaveBeenCalled()
})

test('shows error message when Next is clicked with empty input', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(screen.getByText(/please fill in all fields before continuing/i)).toBeInTheDocument()
})

test('error message does not show before Next is clicked', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.queryByText(/please fill in all fields before continuing/i)).not.toBeInTheDocument()
})

test('error message disappears after filling input and clicking Next', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  // Trigger error
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(screen.getByText(/please fill in all fields before continuing/i)).toBeInTheDocument()

  // Fill in and click Next again
  fireEvent.change(screen.getByRole('textbox'), { target: { value: '100' } })
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(screen.queryByText(/please fill in all fields before continuing/i)).not.toBeInTheDocument()
})

test('onNext is NOT called when only some inputs are filled', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 2,
    bathrooms_to_reno: 0
  }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const inputs = screen.getAllByRole('textbox')
  fireEvent.change(inputs[0], { target: { value: '100' } })

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(mockOnNext).not.toHaveBeenCalled()
})

test('shows error when only some inputs are filled', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 2,
    bathrooms_to_reno: 0
  }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const inputs = screen.getAllByRole('textbox')
  fireEvent.change(inputs[0], { target: { value: '100' } })

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(screen.getByText(/please fill in all fields before continuing/i)).toBeInTheDocument()
})

test('onNext is NOT called when bedroom is filled but bathroom is not', () => {
  const answers = {
    renovation_type: ['Bedroom', 'Bathroom'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 1
  }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const inputs = screen.getAllByRole('textbox')
  fireEvent.change(inputs[0], { target: { value: '100' } })

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(mockOnNext).not.toHaveBeenCalled()
})

test('shows error when bedroom is filled but bathroom is not', () => {
  const answers = {
    renovation_type: ['Bedroom', 'Bathroom'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 1
  }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const inputs = screen.getAllByRole('textbox')
  fireEvent.change(inputs[0], { target: { value: '100' } })

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(screen.getByText(/please fill in all fields before continuing/i)).toBeInTheDocument()
})

// ============================================================
// SECTION 9: Callback Tests — onNext called with correct data
// Values are converted to numbers before being passed
// ============================================================

test('calls onNext with correct sqft_renovated for a single other type', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.change(screen.getByRole('textbox'), { target: { value: '150' } })
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledTimes(1)
  expect(mockOnNext).toHaveBeenCalledWith({
    sqft_renovated: {
      bedrooms: [],
      bathrooms: [],
      other: { Kitchen: 150 }
    }
  })
})

test('calls onNext with 0 when user enters 0', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.change(screen.getByRole('textbox'), { target: { value: '0' } })
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({
    sqft_renovated: {
      bedrooms: [],
      bathrooms: [],
      other: { Kitchen: 0 }
    }
  })
})

test('calls onNext with correct data for a single bedroom', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 0
  }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.change(screen.getByRole('textbox'), { target: { value: '200' } })
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({
    sqft_renovated: {
      bedrooms: [200],
      bathrooms: [],
      other: {}
    }
  })
})

test('calls onNext with correct data for a single bathroom', () => {
  const answers = {
    renovation_type: ['Bathroom'],
    bedrooms_to_reno: 0,
    bathrooms_to_reno: 1
  }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.change(screen.getByRole('textbox'), { target: { value: '80' } })
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({
    sqft_renovated: {
      bedrooms: [],
      bathrooms: [80],
      other: {}
    }
  })
})

test('calls onNext with correct data for bedroom + bathroom + other combined', () => {
  const answers = {
    renovation_type: ['Bedroom', 'Bathroom', 'Kitchen'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 1
  }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const inputs = screen.getAllByRole('textbox')
  fireEvent.change(inputs[0], { target: { value: '100' } })
  fireEvent.change(inputs[1], { target: { value: '50' } })
  fireEvent.change(inputs[2], { target: { value: '200' } })

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({
    sqft_renovated: {
      bedrooms: [100],
      bathrooms: [50],
      other: { Kitchen: 200 }
    }
  })
})

test('calls onNext with correct data for Full renovation', () => {
  const answers = { renovation_type: ['Full renovation'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.change(screen.getByRole('textbox'), { target: { value: '500' } })
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({
    sqft_renovated: {
      bedrooms: [],
      bathrooms: [],
      other: { 'Full renovation': 500 }
    }
  })
})

test('calls onNext with correct data for multiple bedrooms', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 2,
    bathrooms_to_reno: 0
  }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const inputs = screen.getAllByRole('textbox')
  fireEvent.change(inputs[0], { target: { value: '100' } })
  fireEvent.change(inputs[1], { target: { value: '150' } })

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({
    sqft_renovated: {
      bedrooms: [100, 150],
      bathrooms: [],
      other: {}
    }
  })
})

test('calls onNext with correct data for two other renovation types', () => {
  const answers = { renovation_type: ['Kitchen', 'Living room'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const inputs = screen.getAllByRole('textbox')
  fireEvent.change(inputs[0], { target: { value: '120' } })
  fireEvent.change(inputs[1], { target: { value: '90' } })

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({
    sqft_renovated: {
      bedrooms: [],
      bathrooms: [],
      other: { Kitchen: 120, 'Living room': 90 }
    }
  })
})

test('values are passed as numbers not strings', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.change(screen.getByRole('textbox'), { target: { value: '300' } })
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  const arg = mockOnNext.mock.calls[0][0]
  expect(typeof arg.sqft_renovated.other['Kitchen']).toBe('number')
})

test('onNext is called exactly once on valid submission', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.change(screen.getByRole('textbox'), { target: { value: '100' } })
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledTimes(1)
})

// ============================================================
// SECTION 10: onBack Callback Tests
// ============================================================

test('calls onBack when Back button is clicked', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByRole('button', { name: /Back/i }))

  expect(mockOnBack).toHaveBeenCalledTimes(1)
})

test('onNext is NOT called when Back is clicked', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByRole('button', { name: /Back/i }))

  expect(mockOnNext).not.toHaveBeenCalled()
})

// ============================================================
// SECTION 11: Edge Case / Boundary Tests
// ============================================================

test('renders without crashing when answers is undefined', () => {
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={undefined} />)

  expect(screen.getByRole('button', { name: /Back/i })).toBeInTheDocument()
})

test('renders without crashing when renovation_type is empty', () => {
  const answers = { renovation_type: [] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.queryAllByRole('textbox')).toHaveLength(0)
})

test('accepts a very large number like 999999', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const input = screen.getByRole('textbox')
  fireEvent.change(input, { target: { value: '999999' } })

  expect(input.value).toBe('999999')
})

test('accepts 1 as the minimum meaningful value', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const input = screen.getByRole('textbox')
  fireEvent.change(input, { target: { value: '1' } })

  expect(input.value).toBe('1')
})

test('bedroom values are passed as numbers not strings', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 0
  }
  render(<SqftToReno onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.change(screen.getByRole('textbox'), { target: { value: '250' } })
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  const arg = mockOnNext.mock.calls[0][0]
  expect(typeof arg.sqft_renovated.bedrooms[0]).toBe('number')
})