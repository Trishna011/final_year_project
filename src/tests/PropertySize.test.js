import { render, screen, fireEvent } from '@testing-library/react'
import React from "react"
import PropertySize from "../components/PropertySize"

const mockOnNext = jest.fn()
const mockOnBack = jest.fn()

//reset mocks before each test
beforeEach(() => {
  jest.clearAllMocks()
})

//---------------------------
// Basic untit tests of does the page render
//---------------------------

test('renders the heading', () => {
    render(<PropertySize onNext={mockOnNext} onBack={mockOnBack} />)

    //there should be a heading on the screen
    expect(screen.getByText(/what is the property size/i)).toBeInTheDocument()
})

test('input box rendered', () => {
    render(<PropertySize onNext={mockOnNext} onBack={mockOnBack} />)

    expect(screen.getByRole('textbox')).toBeInTheDocument()
})

test('next button rendered', () => {
    render(<PropertySize onNext={mockOnNext} onBack={mockOnBack} />)

    expect(screen.getByRole('button', {name: /Next/i})).toBeInTheDocument() 
})

test('back button rendered', () => {
    render(<PropertySize onNext={mockOnNext} onBack={mockOnBack} />)

    expect(screen.getByRole('button', {name: /Back/i})).toBeInTheDocument() 
})

test('input has correct placeholder text', () => {
    render(<PropertySize onNext={mockOnNext} onBack={mockOnBack} />)

    const input = screen.getByRole('textbox')

    //there should be a placeholder
    expect(input).toHaveAttribute('placeholder', 'Enter the property size in sqft')
})

//---------------------------
// Validation tests
//---------------------------

//valid inputs
test('when the user inputs a number, it shows up in the input box', () => {
    render(<PropertySize onNext={mockOnNext} onBack={mockOnBack} />)

    const input = screen.getByRole('textbox')

    //there should be a placeholder
    expect(input).toHaveAttribute('placeholder', 'Enter the property size in sqft')
    fireEvent.change(input, {target: {value: "12"}})

    expect(input.value).toBe("12")

})

//empty inp
test('Mock next isnt called when input is empty', () => {
    render(<PropertySize onNext={mockOnNext} onBack={mockOnBack} />)

    const input = screen.getByRole('textbox')
    const button = screen.getByRole('button', {name: /Next/i})
    
    //check inp is empty
    expect(input.value).toBe('')

    // button should be disabled
    expect(mockOnNext).not.toHaveBeenCalled()

})

test('shows error message when Next clicked with empty input', () => {
    render(<PropertySize onNext={mockOnNext} onBack={mockOnBack} />)

    // type something then clear it to make button enabled then trigger error
    const input = screen.getByRole('textbox')
    
    // type 0 — this makes canProceed false but triggers the error path
    expect(input.value).toBe('')
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))


    // error msg shuld show
    expect(mockOnNext).not.toHaveBeenCalled()

})

// Zero and negatives (boundary)
test('Next button is disabled when value is 0', () => {
    render(<PropertySize onNext={mockOnNext} onBack={mockOnBack} />)

    const input = screen.getByRole('textbox')

    //there should be a placeholder
    expect(input).toHaveAttribute('placeholder', 'Enter the property size in sqft')
    fireEvent.change(input, {target: {value: "0"}})

    expect(mockOnNext).not.toHaveBeenCalled()

})


//---------------------------
// Negative tests
//---------------------------

test('when the user inputs a letter, it should not show up in input box', () => {
    render(<PropertySize onNext={mockOnNext} onBack={mockOnBack} />)

    const input = screen.getByRole('textbox')

    //there should be a placeholder
    expect(input).toHaveAttribute('placeholder', 'Enter the property size in sqft')
    fireEvent.change(input, {target: {value: "hello"}})

    expect(input.value).toBe("")

})

test('rejects decimal nums', () => {
    render(<PropertySize onNext={mockOnNext} onBack={mockOnBack} />)

    const input = screen.getByRole('textbox')

    //there should be a placeholder
    expect(input).toHaveAttribute('placeholder', 'Enter the property size in sqft')
    fireEvent.change(input, {target: {value: "1.12"}})

    expect(input.value).toBe("")

})

test('rejects special characters like !', () => {
    render(<PropertySize onNext={mockOnNext} onBack={mockOnBack} />)

    const input = screen.getByRole('textbox')

    // first type valid input
    fireEvent.change(input, { target: { value: '123' } })
    expect(input.value).toBe('123')

    // then try to type invalid character
    fireEvent.change(input, { target: { value: '123!' } })

    // value should stay as 123 — the ! gets rejected
    expect(input.value).toBe('123')

})

//---------------------------
// Error message tests
//---------------------------
test('shows "Please enter a value" when empty', () => {
    render(<PropertySize onNext={mockOnNext} onBack={mockOnBack} />)

    const input = screen.getByRole('textbox')

    // confirm input is empty
    expect(input.value).toBe('')

    // click next with empty input
    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    // correct error message should appear
    expect(screen.getByText(/please enter a value/i)).toBeInTheDocument()
})

test('shows "Please enter a number greater than 0" when zero', () => {
    render(<PropertySize onNext={mockOnNext} onBack={mockOnBack} />)

    const input = screen.getByRole('textbox')

    // write 0
    fireEvent.change(input, { target: { value: '0' } })
    expect(input.value).toBe('0')

    // click next with empty input
    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    // correct error message should appear
    expect(screen.getByText(/please enter a number greater than 0/i)).toBeInTheDocument()
})

test('error message pls enter valid inp disappears after valid input is typed', () => {
    render(<PropertySize onNext={mockOnNext} onBack={mockOnBack} />)

    const input = screen.getByRole('textbox')

    // confirm input is empty
    expect(input.value).toBe('')

    // click next with empty input
    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    // correct error message should appear
    expect(screen.getByText(/please enter a value/i)).toBeInTheDocument()

    // write something valid
    fireEvent.change(input, { target: { value: '123' } })
    expect(input.value).toBe('123')

    // correct error message should disapper
    expect(screen.queryByText(/please enter a value/i)).not.toBeInTheDocument()

})

test('error message pls enter num > 0 disappears after valid input is typed', () => {
    render(<PropertySize onNext={mockOnNext} onBack={mockOnBack} />)

    const input = screen.getByRole('textbox')

    // write 0
    fireEvent.change(input, { target: { value: '0' } })
    expect(input.value).toBe('0')

    // click next with empty input
    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    // correct error message should appear
    expect(screen.getByText(/please enter a number greater than 0/i)).toBeInTheDocument()
    // write something valid
    fireEvent.change(input, { target: { value: '123' } })
    expect(input.value).toBe('123')

    // correct error message should disapper
    expect(screen.queryByText(/please enter a number greater than 0/i)).not.toBeInTheDocument()

})

//---------------------------
// Callback Tests
//---------------------------
test('calls onNext with correct property_size as integer', async () => {
  
  render(<PropertySize onNext={mockOnNext} onBack={mockOnBack} />)

  const input = screen.getByRole('textbox')
  const nextButton = screen.getByRole('button', { name: /next/i })

  fireEvent.change(input, { target: { value: '250' } })
  fireEvent.click(screen.getByRole('button', { name: /next/i }))

  expect(mockOnNext).toHaveBeenCalledTimes(1)

  // adjust this shape if your component sends a different payload
  expect(mockOnNext).toHaveBeenCalledWith({
    property_size: 250,
  })

  // extra safety, ensure it is a number
  const callArg = mockOnNext.mock.calls[0][0]
  expect(typeof callArg.property_size).toBe('number')
})

test('calls onBack when Back is clicked', async () => {
  
  render(<PropertySize onNext={mockOnNext} onBack={mockOnBack} />)

  const input = screen.getByRole('textbox')
  
  //click back button
  fireEvent.click(screen.getByRole('button', { name: /Back/i }))

  expect(mockOnBack).toHaveBeenCalledTimes(1)


})

//---------------------------
// Boundary Tests
//---------------------------
test('accepts 1 as the minimum valid value', () => {
    render(<PropertySize onNext={mockOnNext} onBack={mockOnBack} />)

    const input = screen.getByRole('textbox')

    //there should be a placeholder
    expect(input).toHaveAttribute('placeholder', 'Enter the property size in sqft')
    fireEvent.change(input, {target: {value: "1"}})

    expect(input.value).toBe("1")

})

test('accepts a very large number like 999999', () => {
    render(<PropertySize onNext={mockOnNext} onBack={mockOnBack} />)

    const input = screen.getByRole('textbox')

    //there should be a placeholder
    expect(input).toHaveAttribute('placeholder', 'Enter the property size in sqft')
    fireEvent.change(input, {target: {value: "999999"}})

    expect(input.value).toBe("999999")

})
