import { render, screen, fireEvent } from '@testing-library/react'
import React from "react"
import MaterialGrade from "../components/MaterialGrade"

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
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Select Material Grade/i)).toBeInTheDocument()
})

test('renders Next button', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByRole('button', { name: /Next/i })).toBeInTheDocument()
})

test('renders Back button', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByRole('button', { name: /Back/i })).toBeInTheDocument()
})

test('renders a dropdown for a single non-bed/bath renovation type', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  // The dropdown for Kitchen Material should appear
  expect(screen.getByText(/Kitchen Material/i)).toBeInTheDocument()
})

test('renders a dropdown with the correct material options', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/High-end/i)).toBeInTheDocument()
  expect(screen.getByText(/Mid-range/i)).toBeInTheDocument()
  expect(screen.getByText(/Budget-friendly/i)).toBeInTheDocument()
})

// ============================================================
// SECTION 2: Bedroom Rendering Tests
// Verifies that bedroom dropdowns render based on bedrooms_to_reno count
// ============================================================

test('renders the correct number of bedroom dropdowns when bedrooms are selected', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 2,
    bathrooms_to_reno: 0
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Bedroom 1 Material/i)).toBeInTheDocument()
  expect(screen.getByText(/Bedroom 2 Material/i)).toBeInTheDocument()
})

test('renders only 1 bedroom dropdown when bedrooms_to_reno is 1', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 0
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Bedroom 1 Material/i)).toBeInTheDocument()
  expect(screen.queryByText(/Bedroom 2 Material/i)).not.toBeInTheDocument()
})

test('renders 3 bedroom dropdowns when bedrooms_to_reno is 3', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 3,
    bathrooms_to_reno: 0
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Bedroom 1 Material/i)).toBeInTheDocument()
  expect(screen.getByText(/Bedroom 2 Material/i)).toBeInTheDocument()
  expect(screen.getByText(/Bedroom 3 Material/i)).toBeInTheDocument()
})

// ============================================================
// SECTION 3: Bathroom Rendering Tests
// Verifies that bathroom dropdowns render correctly
// ============================================================

test('renders the correct number of bathroom dropdowns', () => {
  const answers = {
    renovation_type: ['Bathroom'],
    bedrooms_to_reno: 0,
    bathrooms_to_reno: 2
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Bathroom 1 Material/i)).toBeInTheDocument()
  expect(screen.getByText(/Bathroom 2 Material/i)).toBeInTheDocument()
})

test('renders only 1 bathroom dropdown when bathrooms_to_reno is 1', () => {
  const answers = {
    renovation_type: ['Bathroom'],
    bedrooms_to_reno: 0,
    bathrooms_to_reno: 1
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Bathroom 1 Material/i)).toBeInTheDocument()
  expect(screen.queryByText(/Bathroom 2 Material/i)).not.toBeInTheDocument()
})

// ============================================================
// SECTION 4: Mixed Bedroom + Bathroom Rendering Tests
// ============================================================

test('renders both bedroom and bathroom dropdowns when both types selected', () => {
  const answers = {
    renovation_type: ['Bedroom', 'Bathroom'],
    bedrooms_to_reno: 2,
    bathrooms_to_reno: 1
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Bedroom 1 Material/i)).toBeInTheDocument()
  expect(screen.getByText(/Bedroom 2 Material/i)).toBeInTheDocument()
  expect(screen.getByText(/Bathroom 1 Material/i)).toBeInTheDocument()
})

test('renders bedroom, bathroom AND other type dropdowns when all are selected', () => {
  const answers = {
    renovation_type: ['Bedroom', 'Bathroom', 'Kitchen'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 1
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Bedroom 1 Material/i)).toBeInTheDocument()
  expect(screen.getByText(/Bathroom 1 Material/i)).toBeInTheDocument()
  expect(screen.getByText(/Kitchen Material/i)).toBeInTheDocument()
})

// ============================================================
// SECTION 5: Full Renovation Tests
// "Full renovation" should show only one dropdown and override all others
// ============================================================

test('renders only one dropdown for Full renovation', () => {
  const answers = {
    renovation_type: ['Full renovation'],
    bedrooms_to_reno: 0,
    bathrooms_to_reno: 0
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Full renovation Material/i)).toBeInTheDocument()
})

test('does not render bedroom dropdowns when Full renovation is selected', () => {
  const answers = {
    renovation_type: ['Full renovation'],
    bedrooms_to_reno: 2,
    bathrooms_to_reno: 2
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.queryByText(/Bedroom 1 Material/i)).not.toBeInTheDocument()
  expect(screen.queryByText(/Bathroom 1 Material/i)).not.toBeInTheDocument()
})

test('does not render other reno type dropdowns when Full renovation is selected', () => {
  const answers = {
    renovation_type: ['Full renovation', 'Kitchen'],
    bedrooms_to_reno: 0,
    bathrooms_to_reno: 0
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  // Kitchen should NOT appear — full reno dominates
  expect(screen.queryByText(/Kitchen Material/i)).not.toBeInTheDocument()
  expect(screen.getByText(/Full renovation Material/i)).toBeInTheDocument()
})

// ============================================================
// SECTION 6: Dropdown Default Value Tests
// All dropdowns should default to empty ("Choose material grade")
// ============================================================

test('bedroom dropdown defaults to placeholder text', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 0
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const select = screen.getAllByRole('combobox')[0]
  expect(select.value).toBe('')
})

test('bathroom dropdown defaults to placeholder text', () => {
  const answers = {
    renovation_type: ['Bathroom'],
    bedrooms_to_reno: 0,
    bathrooms_to_reno: 1
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const select = screen.getAllByRole('combobox')[0]
  expect(select.value).toBe('')
})

test('other renovation type dropdown defaults to placeholder text', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const select = screen.getAllByRole('combobox')[0]
  expect(select.value).toBe('')
})

// ============================================================
// SECTION 7: Dropdown Selection Tests
// Verifies user can change a dropdown value
// ============================================================

test('user can select High-end for a bedroom dropdown', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 0
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const select = screen.getAllByRole('combobox')[0]
  fireEvent.change(select, { target: { value: 'High-end' } })

  expect(select.value).toBe('High-end')
})

test('user can select Mid-range for a bathroom dropdown', () => {
  const answers = {
    renovation_type: ['Bathroom'],
    bedrooms_to_reno: 0,
    bathrooms_to_reno: 1
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const select = screen.getAllByRole('combobox')[0]
  fireEvent.change(select, { target: { value: 'Mid-range' } })

  expect(select.value).toBe('Mid-range')
})

test('user can select Budget-friendly for Full renovation', () => {
  const answers = {
    renovation_type: ['Full renovation'],
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const select = screen.getAllByRole('combobox')[0]
  fireEvent.change(select, { target: { value: 'Budget-friendly' } })

  expect(select.value).toBe('Budget-friendly')
})

test('user can select different grades for multiple dropdowns independently', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 2,
    bathrooms_to_reno: 0
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const selects = screen.getAllByRole('combobox')
  fireEvent.change(selects[0], { target: { value: 'High-end' } })
  fireEvent.change(selects[1], { target: { value: 'Budget-friendly' } })

  expect(selects[0].value).toBe('High-end')
  expect(selects[1].value).toBe('Budget-friendly')
})

// ============================================================
// SECTION 8: Validation / Error Message Tests
// Next button is always clickable — errors show as messages, not disabled state
// ============================================================

test('Next button is never disabled', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const button = screen.getByRole('button', { name: /Next/i })
  expect(button).not.toBeDisabled()
})

test('onNext is NOT called when a dropdown is still unselected', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).not.toHaveBeenCalled()
})

test('shows error message when Next is clicked with no dropdown selected', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(screen.getByText(/please select a material grade for all rooms/i)).toBeInTheDocument()
})

test('error message does not show before Next is clicked', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.queryByText(/please select a material grade for all rooms/i)).not.toBeInTheDocument()
})

test('error message disappears after valid selection and clicking Next', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  // Trigger the error
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(screen.getByText(/please select a material grade for all rooms/i)).toBeInTheDocument()

  // Make a valid selection then click Next — error should clear
  fireEvent.change(screen.getAllByRole('combobox')[0], { target: { value: 'Mid-range' } })
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(screen.queryByText(/please select a material grade for all rooms/i)).not.toBeInTheDocument()
})

test('onNext is NOT called when only some dropdowns are filled (mixed reno types)', () => {
  const answers = {
    renovation_type: ['Bedroom', 'Kitchen'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 0
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const selects = screen.getAllByRole('combobox')
  // Only fill the first dropdown, leave the second blank
  fireEvent.change(selects[0], { target: { value: 'High-end' } })

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(mockOnNext).not.toHaveBeenCalled()
})

test('shows error when only some dropdowns are filled in mixed reno types', () => {
  const answers = {
    renovation_type: ['Bedroom', 'Kitchen'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 0
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const selects = screen.getAllByRole('combobox')
  fireEvent.change(selects[0], { target: { value: 'High-end' } })

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(screen.getByText(/please select a material grade for all rooms/i)).toBeInTheDocument()
})

test('onNext is NOT called when bedroom is filled but bathroom is not', () => {
  const answers = {
    renovation_type: ['Bedroom', 'Bathroom'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 1
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const selects = screen.getAllByRole('combobox')
  fireEvent.change(selects[0], { target: { value: 'High-end' } })

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(mockOnNext).not.toHaveBeenCalled()
})

test('shows error when bedroom is filled but bathroom is not', () => {
  const answers = {
    renovation_type: ['Bedroom', 'Bathroom'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 1
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const selects = screen.getAllByRole('combobox')
  fireEvent.change(selects[0], { target: { value: 'High-end' } })

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(screen.getByText(/please select a material grade for all rooms/i)).toBeInTheDocument()
})

// ============================================================
// SECTION 9: Callback Tests (onNext called with correct data)
// ============================================================

test('calls onNext with correct material_grade for a single other reno type', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const select = screen.getAllByRole('combobox')[0]
  fireEvent.change(select, { target: { value: 'Mid-range' } })

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledTimes(1)
  expect(mockOnNext).toHaveBeenCalledWith({
    material_grade: {
      bedrooms: [],
      bathrooms: [],
      other: { Kitchen: 'Mid-range' }
    }
  })
})

test('calls onNext with correct material_grade for a single bedroom', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 0
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const select = screen.getAllByRole('combobox')[0]
  fireEvent.change(select, { target: { value: 'High-end' } })

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledTimes(1)
  expect(mockOnNext).toHaveBeenCalledWith({
    material_grade: {
      bedrooms: ['High-end'],
      bathrooms: [],
      other: {}
    }
  })
})

test('calls onNext with correct material_grade for a single bathroom', () => {
  const answers = {
    renovation_type: ['Bathroom'],
    bedrooms_to_reno: 0,
    bathrooms_to_reno: 1
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const select = screen.getAllByRole('combobox')[0]
  fireEvent.change(select, { target: { value: 'Budget-friendly' } })

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledTimes(1)
  expect(mockOnNext).toHaveBeenCalledWith({
    material_grade: {
      bedrooms: [],
      bathrooms: ['Budget-friendly'],
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
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const selects = screen.getAllByRole('combobox')
  // Order: bedroom 1, bathroom 1, Kitchen (other)
  fireEvent.change(selects[0], { target: { value: 'High-end' } })
  fireEvent.change(selects[1], { target: { value: 'Mid-range' } })
  fireEvent.change(selects[2], { target: { value: 'Budget-friendly' } })

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledTimes(1)
  expect(mockOnNext).toHaveBeenCalledWith({
    material_grade: {
      bedrooms: ['High-end'],
      bathrooms: ['Mid-range'],
      other: { Kitchen: 'Budget-friendly' }
    }
  })
})

test('calls onNext with correct data for Full renovation', () => {
  const answers = {
    renovation_type: ['Full renovation'],
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const select = screen.getAllByRole('combobox')[0]
  fireEvent.change(select, { target: { value: 'High-end' } })

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledTimes(1)
  expect(mockOnNext).toHaveBeenCalledWith({
    material_grade: {
      bedrooms: [],
      bathrooms: [],
      other: { 'Full renovation': 'High-end' }
    }
  })
})

test('calls onNext with correct data for multiple bedrooms', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 2,
    bathrooms_to_reno: 0
  }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const selects = screen.getAllByRole('combobox')
  fireEvent.change(selects[0], { target: { value: 'High-end' } })
  fireEvent.change(selects[1], { target: { value: 'Budget-friendly' } })

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledTimes(1)
  expect(mockOnNext).toHaveBeenCalledWith({
    material_grade: {
      bedrooms: ['High-end', 'Budget-friendly'],
      bathrooms: [],
      other: {}
    }
  })
})

test('onNext is called exactly once when all fields are valid', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.change(screen.getAllByRole('combobox')[0], { target: { value: 'Mid-range' } })
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledTimes(1)
})

// ============================================================
// SECTION 10: onBack Callback Tests
// ============================================================

test('calls onBack when Back button is clicked', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByRole('button', { name: /Back/i }))

  expect(mockOnBack).toHaveBeenCalledTimes(1)
})

test('onNext is NOT called when Back is clicked', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByRole('button', { name: /Back/i }))

  expect(mockOnNext).not.toHaveBeenCalled()
})

// ============================================================
// SECTION 11: Edge Case / Boundary Tests
// Handles unusual or extreme props gracefully
// ============================================================

test('renders without crashing when answers is undefined', () => {
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={undefined} />)

  // With no renovation types, no dropdowns should be shown but it shouldn't crash
  expect(screen.getByRole('button', { name: /Back/i })).toBeInTheDocument()
})

test('renders the correct number of dropdowns for two other renovation types', () => {
  const answers = { renovation_type: ['Kitchen', 'Living room'] }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Kitchen Material/i)).toBeInTheDocument()
  expect(screen.getByText(/Living room Material/i)).toBeInTheDocument()
})

test('calls onNext with correct data for two other renovation types', () => {
  const answers = { renovation_type: ['Kitchen', 'Living room'] }
  render(<MaterialGrade onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const selects = screen.getAllByRole('combobox')
  fireEvent.change(selects[0], { target: { value: 'High-end' } })
  fireEvent.change(selects[1], { target: { value: 'Mid-range' } })

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({
    material_grade: {
      bedrooms: [],
      bathrooms: [],
      other: { Kitchen: 'High-end', 'Living room': 'Mid-range' }
    }
  })
})
