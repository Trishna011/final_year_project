import { render, screen, fireEvent } from '@testing-library/react'
import React from "react"
import StructChanges from "../components/StructChanges"

const mockOnNext = jest.fn()
const mockOnBack = jest.fn()

beforeEach(() => {
  jest.clearAllMocks()
})

// ============================================================
// SECTION 1: Basic Rendering Tests
// Verifies the component mounts and core UI elements are present
// ============================================================

test('renders the heading', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Any structural changes required\?/i)).toBeInTheDocument()
})

test('renders the Next button', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByRole('button', { name: /Next/i })).toBeInTheDocument()
})

test('renders the Back button', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByRole('button', { name: /Back/i })).toBeInTheDocument()
})

test('renders Yes and No options for a single room', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/^Yes$/i)).toBeInTheDocument()
  expect(screen.getByText(/^No$/i)).toBeInTheDocument()
})

test('renders the room label for a single other renovation type', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/^Kitchen$/i)).toBeInTheDocument()
})

// ============================================================
// SECTION 2: Bedroom Card Rendering Tests
// Verifies bedroom cards render based on bedrooms_to_reno count
// ============================================================

test('renders the correct number of bedroom cards', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 2,
    bathrooms_to_reno: 0
  }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Bedroom 1/i)).toBeInTheDocument()
  expect(screen.getByText(/Bedroom 2/i)).toBeInTheDocument()
})

test('renders only 1 bedroom card when bedrooms_to_reno is 1', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 0
  }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Bedroom 1/i)).toBeInTheDocument()
  expect(screen.queryByText(/Bedroom 2/i)).not.toBeInTheDocument()
})

test('renders 3 bedroom cards when bedrooms_to_reno is 3', () => {
  const answers = {
    renovation_type: ['Bedroom'],
    bedrooms_to_reno: 3,
    bathrooms_to_reno: 0
  }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Bedroom 1/i)).toBeInTheDocument()
  expect(screen.getByText(/Bedroom 2/i)).toBeInTheDocument()
  expect(screen.getByText(/Bedroom 3/i)).toBeInTheDocument()
})

// ============================================================
// SECTION 3: Bathroom Card Rendering Tests
// ============================================================

test('renders the correct number of bathroom cards', () => {
  const answers = {
    renovation_type: ['Bathroom'],
    bedrooms_to_reno: 0,
    bathrooms_to_reno: 2
  }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Bathroom 1/i)).toBeInTheDocument()
  expect(screen.getByText(/Bathroom 2/i)).toBeInTheDocument()
})

test('renders only 1 bathroom card when bathrooms_to_reno is 1', () => {
  const answers = {
    renovation_type: ['Bathroom'],
    bedrooms_to_reno: 0,
    bathrooms_to_reno: 1
  }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Bathroom 1/i)).toBeInTheDocument()
  expect(screen.queryByText(/Bathroom 2/i)).not.toBeInTheDocument()
})

// ============================================================
// SECTION 4: Mixed Room Rendering Tests
// ============================================================

test('renders bedroom, bathroom and other room cards when all selected', () => {
  const answers = {
    renovation_type: ['Bedroom', 'Bathroom', 'Kitchen'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 1
  }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/Bedroom 1/i)).toBeInTheDocument()
  expect(screen.getByText(/Bathroom 1/i)).toBeInTheDocument()
  expect(screen.getByText(/^Kitchen$/i)).toBeInTheDocument()
})

test('renders two other renovation type cards', () => {
  const answers = { renovation_type: ['Kitchen', 'Living room'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/^Kitchen$/i)).toBeInTheDocument()
  expect(screen.getByText(/^Living room$/i)).toBeInTheDocument()
})

test('renders Yes and No options for each room', () => {
  const answers = { renovation_type: ['Kitchen', 'Living room'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  // 2 rooms × 2 options = 4 Yes/No elements
  expect(screen.getAllByText(/^Yes$/i)).toHaveLength(2)
  expect(screen.getAllByText(/^No$/i)).toHaveLength(2)
})

// ============================================================
// SECTION 5: Full Renovation Tests
// Full renovation shows only one card
// ============================================================

test('renders only one card for Full renovation', () => {
  const answers = { renovation_type: ['Full renovation'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByText(/^Full renovation$/i)).toBeInTheDocument()
  expect(screen.getAllByText(/^Yes$/i)).toHaveLength(1)
  expect(screen.getAllByText(/^No$/i)).toHaveLength(1)
})

test('does not render bedroom cards when Full renovation is selected', () => {
  const answers = {
    renovation_type: ['Full renovation'],
    bedrooms_to_reno: 2,
    bathrooms_to_reno: 2
  }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.queryByText(/Bedroom 1/i)).not.toBeInTheDocument()
  expect(screen.queryByText(/Bathroom 1/i)).not.toBeInTheDocument()
})

// ============================================================
// SECTION 6: Validation / Error Message Tests
// Next button is always clickable — shows error if not all rooms answered
// ============================================================

test('Next button is never disabled', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.getByRole('button', { name: /Next/i })).not.toBeDisabled()
})

test('onNext is NOT called when no room is answered', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).not.toHaveBeenCalled()
})

test('shows error message when Next is clicked with unanswered rooms', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(screen.getByText(/please answer all rooms before continuing/i)).toBeInTheDocument()
})

test('error message does not show before Next is clicked', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  expect(screen.queryByText(/please answer all rooms before continuing/i)).not.toBeInTheDocument()
})

test('error message disappears after all rooms are answered and Next is clicked', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  // Trigger error
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(screen.getByText(/please answer all rooms before continuing/i)).toBeInTheDocument()

  // Answer the room and click Next again
  fireEvent.click(screen.getByText(/^Yes$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(screen.queryByText(/please answer all rooms before continuing/i)).not.toBeInTheDocument()
})

test('error message disappears immediately after selecting an option following a failed submission', () => {
  const answers = { renovation_type: ['Kitchen'] }

  render(
    <StructChanges
      onNext={mockOnNext}
      onBack={mockOnBack}
      answers={answers}
    />
  )

  // Click Next without answering → trigger error
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  // Error should appear
  expect(
    screen.getByText(/please answer all rooms before continuing/i)
  ).toBeInTheDocument()

  // Select an option
  fireEvent.click(screen.getByText(/^Yes$/i))

  // Error should disappear immediately
  expect(
    screen.queryByText(/please answer all rooms before continuing/i)
  ).not.toBeInTheDocument()
})

test('onNext is NOT called when only some rooms are answered', () => {
  const answers = { renovation_type: ['Kitchen', 'Living room'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  // Answer only the first room
  fireEvent.click(screen.getAllByText(/^Yes$/i)[0])

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(mockOnNext).not.toHaveBeenCalled()
})

test('shows error when only some rooms are answered', () => {
  const answers = { renovation_type: ['Kitchen', 'Living room'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getAllByText(/^Yes$/i)[0])

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  expect(screen.getByText(/please answer all rooms before continuing/i)).toBeInTheDocument()
})

// ============================================================
// SECTION 7: Selection Behaviour Tests
// Yes/No cards can be selected per room
// ============================================================

test('clicking Yes selects it for a room', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByText(/^Yes$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({ structural_changes: ['Yes'] })
})

test('clicking No selects it for a room', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByText(/^No$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({ structural_changes: ['No'] })
})

test('can switch selection from Yes to No for a room', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByText(/^Yes$/i))
  fireEvent.click(screen.getByText(/^No$/i))

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({ structural_changes: ['No'] })
})

test('can switch selection from No to Yes for a room', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByText(/^No$/i))
  fireEvent.click(screen.getByText(/^Yes$/i))

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({ structural_changes: ['Yes'] })
})

test('each room can be answered independently', () => {
  const answers = { renovation_type: ['Kitchen', 'Living room'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const yesButtons = screen.getAllByText(/^Yes$/i)
  const noButtons = screen.getAllByText(/^No$/i)

  fireEvent.click(yesButtons[0])  // Kitchen → Yes
  fireEvent.click(noButtons[1])   // Living room → No

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({ structural_changes: ['Yes', 'No'] })
})

// ============================================================
// SECTION 8: Callback Tests — onNext called with correct data
// ============================================================

test('calls onNext with correct data for a single room answered Yes', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByText(/^Yes$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledTimes(1)
  expect(mockOnNext).toHaveBeenCalledWith({ structural_changes: ['Yes'] })
})

test('calls onNext with correct data for multiple rooms', () => {
  const answers = {
    renovation_type: ['Bedroom', 'Bathroom'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 1
  }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const yesButtons = screen.getAllByText(/^Yes$/i)
  const noButtons = screen.getAllByText(/^No$/i)

  fireEvent.click(yesButtons[0])  // Bedroom 1 → Yes
  fireEvent.click(noButtons[1])   // Bathroom 1 → No

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({ structural_changes: ['Yes', 'No'] })
})

test('calls onNext with correct data for Full renovation answered Yes', () => {
  const answers = { renovation_type: ['Full renovation'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByText(/^Yes$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({ structural_changes: ['Yes'] })
})

test('calls onNext with correct data for Full renovation answered No', () => {
  const answers = { renovation_type: ['Full renovation'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByText(/^No$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({ structural_changes: ['No'] })
})

test('calls onNext with correct data for bedroom + bathroom + other', () => {
  const answers = {
    renovation_type: ['Bedroom', 'Bathroom', 'Kitchen'],
    bedrooms_to_reno: 1,
    bathrooms_to_reno: 1
  }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const yesButtons = screen.getAllByText(/^Yes$/i)
  const noButtons = screen.getAllByText(/^No$/i)

  fireEvent.click(yesButtons[0])  // Bedroom 1 → Yes
  fireEvent.click(noButtons[1])   // Bathroom 1 → No
  fireEvent.click(yesButtons[2])  // Kitchen → Yes

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledWith({ structural_changes: ['Yes', 'No', 'Yes'] })
})

test('structural_changes is always an array', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByText(/^Yes$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  const arg = mockOnNext.mock.calls[0][0]
  expect(Array.isArray(arg.structural_changes)).toBe(true)
})

test('onNext is called exactly once on valid submission', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByText(/^Yes$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledTimes(1)
})

// ============================================================
// SECTION 9: onBack Callback Tests
// ============================================================

test('calls onBack when Back button is clicked', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByRole('button', { name: /Back/i }))

  expect(mockOnBack).toHaveBeenCalledTimes(1)
})

test('onNext is NOT called when Back is clicked', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByRole('button', { name: /Back/i }))

  expect(mockOnNext).not.toHaveBeenCalled()
})

test('onBack is NOT called when Next is clicked', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByText(/^Yes$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnBack).not.toHaveBeenCalled()
})

// ============================================================
// SECTION 10: Edge Case / Boundary Tests
// ============================================================

test('renders without crashing when answers is undefined', () => {
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={undefined} />)

  expect(screen.getByRole('button', { name: /Back/i })).toBeInTheDocument()
})

test('renders without crashing when renovation_type is empty', () => {
  const answers = { renovation_type: [] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  // No cards rendered, no Yes/No options visible
  expect(screen.queryByText(/^Yes$/i)).not.toBeInTheDocument()
})

test('structural_changes array length matches number of rooms for 3 rooms', () => {
  const answers = { renovation_type: ['Kitchen', 'Living room', 'Other/Custom'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  const yesButtons = screen.getAllByText(/^Yes$/i)
  yesButtons.forEach(btn => fireEvent.click(btn))

  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext.mock.calls[0][0].structural_changes).toHaveLength(3)
})

test('Full renovation structural_changes array has exactly 1 item', () => {
  const answers = { renovation_type: ['Full renovation'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByText(/^Yes$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext.mock.calls[0][0].structural_changes).toHaveLength(1)
})

test('clicking Next multiple times with all rooms answered calls onNext each time', () => {
  const answers = { renovation_type: ['Kitchen'] }
  render(<StructChanges onNext={mockOnNext} onBack={mockOnBack} answers={answers} />)

  fireEvent.click(screen.getByText(/^Yes$/i))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))
  fireEvent.click(screen.getByRole('button', { name: /Next/i }))

  expect(mockOnNext).toHaveBeenCalledTimes(2)
})