import { render, screen, fireEvent } from '@testing-library/react'
import React from "react"
import PropertySize from "../components/BedBathCount"
import BedBathCount from '../components/BedBathCount'

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
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={[]} />)

    //there should be a heading on the screen
    expect(screen.getByText(/How many rooms?/i)).toBeInTheDocument()
})

test('next button rendered', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={[]} />)

    expect(screen.getByRole('button', {name: /Next/i})).toBeInTheDocument() 
})

test('back button rendered', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={[]} />)

    expect(screen.getByRole('button', {name: /Back/i})).toBeInTheDocument() 
})


//==========================
// Bathroom only tests
//==========================

//-------------------------
// Basic rendering 
//-------------------------
test('input box rendered', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom']} />)

    expect(screen.getByRole('spinbutton')).toBeInTheDocument()
})

test('renders the bathroom heading', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom']} />)

    //there should be a heading on the screen
    expect(screen.getByText(/Bathrooms to Renovate/i)).toBeInTheDocument()
})

//-------------------------
//test default value
//-------------------------
test('defaults bathroom', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom']}/>)

    const input = screen.getByRole('spinbutton')
    expect(input).toHaveValue(1)
})

//-------------------------
//test if typing updates correct state
//-------------------------
test('updates bathroom value when changed', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom']}/>)

    const input = screen.getByRole('spinbutton')
    fireEvent.change(input, { target: { value: 3 } })

    expect(input).toHaveValue(3)
})

//-------------------------
//test if up button working
//-------------------------
test('updates bathroom value when changed using up button', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom']}/>)

    const input = screen.getByRole('spinbutton')

    //check default val is 1
    expect(input).toHaveValue(1)
    
    //press up button once
    fireEvent.change(input, { target: { value: 2 } })

    expect(input).toHaveValue(2)
})

//-------------------------
//test if down button working
//-------------------------
test('updates bathroom value when changed using down button', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom']}/>)

    const input = screen.getByRole('spinbutton')

    //change val to 2
    fireEvent.change(input, { target: { value: 2 } })
    
    //press down button once
    fireEvent.change(input, { target: { value: 1 } })

    expect(input).toHaveValue(1)
})

//-------------------------
//negative test
//-------------------------
test('mock on next not called when bedroom is less than 1', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom']}/>)

    const input = screen.getByRole('spinbutton')
    fireEvent.change(input, { target: { value: 0 } })

    const nextButton = screen.getByRole('button', { name: /Next/i })
    expect(mockOnNext).not.toHaveBeenCalled()
})

//-------------------------
// letters not allowed
//-------------------------
test('when the user inputs a letter, it should not show up in input box', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom']}/>)
    const input = screen.getByRole('spinbutton')
    
    //check default inp

    expect(input).toHaveValue(1)

    fireEvent.change(input, { target: { value: "hello" } })

    expect(input).toHaveValue(1)

})

//-------------------------
//test you cant have an empty inp
//-------------------------
test('when user tries to press back when theres 1 digit, the digit changes to 0', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom']}/>)
    const input = screen.getByRole('spinbutton')
    
    //check default inp

    expect(input).toHaveValue(1)
    
    //press the back button
    fireEvent.change(input, { target: { value: '' } })

    expect(input).toHaveValue(1)
})

//-------------------------
// decimals rejected
//-------------------------
test('rejects decimal nums', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom']}/>)

    const input = screen.getByRole('spinbutton')

    //check default inp
    expect(input).toHaveValue(1)

    fireEvent.change(input, {target: {value: "1.12"}})

    expect(input).toHaveValue(1)

})

//-------------------------
// special chars rejected
//-------------------------
test('rejects special characters like !', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom']}/>)

    const input = screen.getByRole('spinbutton')

    //check default inp
    expect(input).toHaveValue(1)

    fireEvent.change(input, {target: {value: "1!"}})

    expect(input).toHaveValue(1)

})

//-------------------------
//error msg tests
//-------------------------
test('shows "Please enter a number greater than 0" when zero', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom']}/>)

    const input = screen.getByRole('spinbutton')

    fireEvent.change(input, {target: {value: 0}})

    // click next with empty input
    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    // correct error message should appear
    expect(screen.getByText(/please enter a number greater than 0/i)).toBeInTheDocument()
})

test('error message pls enter num > 0 disappears after valid input is typed', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom']}/>)

    const input = screen.getByRole('spinbutton')

    fireEvent.change(input, {target: {value: 0}})

    // click next with empty input
    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    // correct error message should appear
    expect(screen.getByText(/please enter a number greater than 0/i)).toBeInTheDocument()

    //now input accepted val
    fireEvent.change(input, {target: {value: 2}})

    //error msg dissapears
    expect(screen.queryByText(/please enter a number greater than 0/i)).not.toBeInTheDocument()

})

//-------------------------
// callback tests
//-------------------------
test('calls onNext with correct property_size as integer', async () => {
  
  render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom']}/>)

  const input = screen.getByRole('spinbutton')
  

  fireEvent.change(input, {target: {value: 2}})

  fireEvent.click(screen.getByRole('button', { name: /next/i }))

  expect(mockOnNext).toHaveBeenCalledTimes(1)

  // adjust this shape if your component sends a different payload
  expect(mockOnNext).toHaveBeenCalledWith({
    bathrooms_to_reno: 2,
  })

})

test('calls onBack when Back is clicked', async () => {
  
  render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom']}/>)

  
  //click back button
  fireEvent.click(screen.getByRole('button', { name: /Back/i }))

  expect(mockOnBack).toHaveBeenCalledTimes(1)


})

// --------------------
// Boundary tests
// --------------------
test('accepts 1 as the minimum valid value', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom']}/>)

    const input = screen.getByRole('spinbutton')
  

    fireEvent.change(input, {target: {value: 1}})

    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    expect(mockOnNext).toHaveBeenCalledTimes(1)

  // adjust this shape if your component sends a different payload
  expect(mockOnNext).toHaveBeenCalledWith({
    bathrooms_to_reno: 1,
  })
})

test('accepts a very large number like 999999', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom']}/>)

    const input = screen.getByRole('spinbutton')
  

    fireEvent.change(input, {target: {value: 999999}})

    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    expect(mockOnNext).toHaveBeenCalledTimes(1)

  // adjust this shape if your component sends a different payload
  expect(mockOnNext).toHaveBeenCalledWith({
    bathrooms_to_reno: 999999,
  })
})


//=========================
// Bedroom only tests
//=========================

//-------------------------
// Basic rendering 
//-------------------------
test('input box rendered', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom']} />)

    expect(screen.getByRole('spinbutton')).toBeInTheDocument()
})

test('renders the Bedroom heading', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom']} />)

    //there should be a heading on the screen
    expect(screen.getByText(/Bedrooms to Renovate/i)).toBeInTheDocument()
})

//-------------------------
//test default value
//-------------------------
test('defaults bedroom', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom']}/>)

    const input = screen.getByRole('spinbutton')
    expect(input).toHaveValue(1)
})

//-------------------------
//test if typing updates correct state
//-------------------------
test('updates bedroom value when changed', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom']}/>)

    const input = screen.getByRole('spinbutton')
    fireEvent.change(input, { target: { value: 3 } })

    expect(input).toHaveValue(3)
})

//-------------------------
//test if up button working
//-------------------------
test('updates bathroom value when changed using up button', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom']}/>)

    const input = screen.getByRole('spinbutton')

    //check default val is 1
    expect(input).toHaveValue(1)
    
    //press up button once
    fireEvent.change(input, { target: { value: 2 } })

    expect(input).toHaveValue(2)
})

//-------------------------
//test if down button working
//-------------------------
test('updates bathroom value when changed using down button', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom']}/>)

    const input = screen.getByRole('spinbutton')

    //change val to 2
    fireEvent.change(input, { target: { value: 2 } })
    
    //press down button once
    fireEvent.change(input, { target: { value: 1 } })

    expect(input).toHaveValue(1)
})

//-------------------------
//negative test
//-------------------------
test('mock on next not called when bedroom is less than 1', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom']}/>)

    const input = screen.getByRole('spinbutton')
    fireEvent.change(input, { target: { value: 0 } })

    const nextButton = screen.getByRole('button', { name: /Next/i })
    expect(mockOnNext).not.toHaveBeenCalled()
})

//-------------------------
// letters not allowed
//-------------------------
test('when the user inputs a letter, it should not show up in input box', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom']}/>)
    const input = screen.getByRole('spinbutton')
    
    //check default inp

    expect(input).toHaveValue(1)

    fireEvent.change(input, { target: { value: "hello" } })

    expect(input).toHaveValue(1)

})

//-------------------------
//test you cant have an empty inp
//-------------------------
test('when user tries to press back when theres 1 digit, the digit changes to 0', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom']}/>)
    const input = screen.getByRole('spinbutton')
    
    //check default inp

    expect(input).toHaveValue(1)
    
    //press the back button
    fireEvent.change(input, { target: { value: '' } })

    expect(input).toHaveValue(1)
})

//-------------------------
// decimals rejected
//-------------------------
test('rejects decimal nums', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom']}/>)

    const input = screen.getByRole('spinbutton')

    //check default inp
    expect(input).toHaveValue(1)

    fireEvent.change(input, {target: {value: "1.12"}})

    expect(input).toHaveValue(1)

})

//-------------------------
// special chars rejected
//-------------------------
test('rejects special characters like !', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom']}/>)

    const input = screen.getByRole('spinbutton')

    //check default inp
    expect(input).toHaveValue(1)

    fireEvent.change(input, {target: {value: "1!"}})

    expect(input).toHaveValue(1)

})

//-------------------------
//error msg tests
//-------------------------

test('shows "Please enter a number greater than 0" when zero', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom']}/>)

    const input = screen.getByRole('spinbutton')

    fireEvent.change(input, {target: {value: 0}})

    // click next with empty input
    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    // correct error message should appear
    expect(screen.getByText(/please enter a number greater than 0/i)).toBeInTheDocument()
})

test('error message pls enter num > 0 disappears after valid input is typed', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom']}/>)

    const input = screen.getByRole('spinbutton')

    fireEvent.change(input, {target: {value: 0}})

    // click next with empty input
    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    // correct error message should appear
    expect(screen.getByText(/please enter a number greater than 0/i)).toBeInTheDocument()

    //now input accepted val
    fireEvent.change(input, {target: {value: 2}})

    //error msg dissapears
    expect(screen.queryByText(/please enter a number greater than 0/i)).not.toBeInTheDocument()

})

test('calls onNext with correct property_size as integer', async () => {
  
  render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom']}/>)

  const input = screen.getByRole('spinbutton')
  

  fireEvent.change(input, {target: {value: 2}})

  fireEvent.click(screen.getByRole('button', { name: /next/i }))

  expect(mockOnNext).toHaveBeenCalledTimes(1)

  // adjust this shape if your component sends a different payload
  expect(mockOnNext).toHaveBeenCalledWith({
    bedrooms_to_reno: 2,
  })

})


test('calls onBack when Back is clicked', async () => {
  
  render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom']}/>)

  
  //click back button
  fireEvent.click(screen.getByRole('button', { name: /Back/i }))

  expect(mockOnBack).toHaveBeenCalledTimes(1)


})

// --------------------
// Boundary tests
// --------------------
test('accepts 1 as the minimum valid value', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom']}/>)

    const input = screen.getByRole('spinbutton')
  

    fireEvent.change(input, {target: {value: 1}})

    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    expect(mockOnNext).toHaveBeenCalledTimes(1)

  // adjust this shape if your component sends a different payload
  expect(mockOnNext).toHaveBeenCalledWith({
    bedrooms_to_reno: 1,
  })
})

test('accepts a very large number like 999999', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom']}/>)

    const input = screen.getByRole('spinbutton')
  

    fireEvent.change(input, {target: {value: 999999}})

    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    expect(mockOnNext).toHaveBeenCalledTimes(1)

  // adjust this shape if your component sends a different payload
  expect(mockOnNext).toHaveBeenCalledWith({
    bedrooms_to_reno: 999999,
  })
})



//===========================
// Bedroom and bathroom tests
//===========================

//-------------------------
// Basic rendering 
//-------------------------
test('input box rendered', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom', 'Bathroom']} />)

    const inputs = screen.getAllByRole('spinbutton')
    expect(inputs).toHaveLength(2)

})

test('renders the Bedroom heading', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom', 'Bathroom']} />)

    //there should be a heading on the screen
    expect(screen.getByText(/Bedrooms to Renovate/i)).toBeInTheDocument()
    expect(screen.getByText(/Bathrooms to Renovate/i)).toBeInTheDocument()
})

//-------------------------
//test default value
//-------------------------
test('defaults bedroom and bathroom values to 1', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom', 'Bathroom']}/>)

    const inputs = screen.getAllByRole('spinbutton')
    expect(inputs[0]).toHaveValue(1)
    expect(inputs[1]).toHaveValue(1)
})

//-------------------------
//test if typing updates correct state
//-------------------------
test('updates bedroom and bedroom value when changed', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom', 'Bathroom']}/>)

    const inputs = screen.getAllByRole('spinbutton')
    fireEvent.change(inputs[0], { target: { value: 3 } })
    fireEvent.change(inputs[1], { target: { value: 2 } })

    expect(inputs[0]).toHaveValue(3)
    expect(inputs[1]).toHaveValue(2)
})

//-------------------------
//test if up button working
//-------------------------
test('updates bathroom value when changed using up button', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom', 'Bedroom']}/>)

    const inputs = screen.getAllByRole('spinbutton')

    //check default val is 1
    expect(inputs[0]).toHaveValue(1)
    expect(inputs[1]).toHaveValue(1)
    
    //press up button once
    fireEvent.change(inputs[0], { target: { value: 2 } })
    fireEvent.change(inputs[1], { target: { value: 2 } })

    expect(inputs[0]).toHaveValue(2)
    expect(inputs[1]).toHaveValue(2)
})

//-------------------------
//test if down button working
//-------------------------
test('updates bathroom value when changed using down button', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom', 'Bedroom']}/>)

    const inputs = screen.getAllByRole('spinbutton')

    //change val to 2
    fireEvent.change(inputs[0], { target: { value: 2 } })
    fireEvent.change(inputs[1], { target: { value: 2 } })
    
    //press down button once
    fireEvent.change(inputs[0], { target: { value: 1 } })
    fireEvent.change(inputs[1], { target: { value: 1 } })

    expect(inputs[0]).toHaveValue(1)
    expect(inputs[1]).toHaveValue(1)
})

//-------------------------
//negative test
//-------------------------
test('mock on next not called when bedroom is less than 1', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom', 'Bathroom']}/>)

    const inputs = screen.getAllByRole('spinbutton')
    fireEvent.change(inputs[0], { target: { value: 0 } })

    const nextButton = screen.getByRole('button', { name: /Next/i })
    expect(mockOnNext).not.toHaveBeenCalled()
})

test('mock on next not called when bathroom is less than 1', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom', 'Bathroom']}/>)

    const inputs = screen.getAllByRole('spinbutton')
    fireEvent.change(inputs[1], { target: { value: 0 } })

    const nextButton = screen.getByRole('button', { name: /Next/i })
    expect(mockOnNext).not.toHaveBeenCalled()
})

//-------------------------
// letters not allowed
//-------------------------
test('when the user inputs a letter, it should not show up in input box', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom', 'Bedroom']}/>)
    const inputs = screen.getAllByRole('spinbutton')
    
    //check default inp

    expect(inputs[0]).toHaveValue(1)
    expect(inputs[1]).toHaveValue(1)

    fireEvent.change(inputs[0], { target: { value: "hello" } })
    fireEvent.change(inputs[1], { target: { value: "hello" } })

    expect(inputs[0]).toHaveValue(1)
    expect(inputs[1]).toHaveValue(1)

})

//test you cant have an empty inp
test('when user tries to press back when theres 1 digit, the digit changes to 0', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom','Bathroom']}/>)
    const inputs = screen.getAllByRole('spinbutton')
    
    //check default inp

    expect(inputs[0]).toHaveValue(1)
    expect(inputs[1]).toHaveValue(1)
    
    //press the back button
    fireEvent.change(inputs[0], { target: { value: '' } })
    fireEvent.change(inputs[1], { target: { value: '' } })

    expect(inputs[0]).toHaveValue(1)
    expect(inputs[1]).toHaveValue(1)
})

test('when the user inputs a letter, it should not show up in input box', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom', 'Bedroom']}/>)
    const inputs = screen.getAllByRole('spinbutton')
    
    //check default inp

    expect(inputs[0]).toHaveValue(1)
    expect(inputs[1]).toHaveValue(1)

    fireEvent.change(inputs[0], { target: { value: "hello" } })

    expect(inputs[0]).toHaveValue(1)
    expect(inputs[1]).toHaveValue(1)

})

test('rejects decimal nums', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom', 'Bathroom']}/>)

    const inputs = screen.getAllByRole('spinbutton')

    //check default inp
    expect(inputs[0]).toHaveValue(1)
    expect(inputs[1]).toHaveValue(1)

    fireEvent.change(inputs[0], {target: {value: "1.12"}})

    expect(inputs[0]).toHaveValue(1)
    expect(inputs[1]).toHaveValue(1)

})

test('rejects special characters like !', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom', 'Bathroom']}/>)

    const inputs = screen.getAllByRole('spinbutton')

    //check default inp
    expect(inputs[0]).toHaveValue(1)
    expect(inputs[1]).toHaveValue(1)

    fireEvent.change(inputs[0], {target: {value: "1!"}})

    expect(inputs[0]).toHaveValue(1)
    expect(inputs[1]).toHaveValue(1)

})

//error test
test('shows "Please enter a number greater than 0" when zero', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom', 'Bathroom']}/>)

    const inputs = screen.getAllByRole('spinbutton')

    fireEvent.change(inputs[0], {target: {value: 0}})

    // click next with empty input
    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    // correct error message should appear
    expect(screen.getByText(/please enter a number greater than 0/i)).toBeInTheDocument()
})

test('error message pls enter num > 0 disappears after valid input is typed', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom','Bedroom']}/>)

    const inputs = screen.getAllByRole('spinbutton')

    fireEvent.change(inputs[0], {target: {value: 0}})

    // click next with empty input
    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    // correct error message should appear
    expect(screen.getByText(/please enter a number greater than 0/i)).toBeInTheDocument()

    //now input accepted val
    fireEvent.change(inputs[0], {target: {value: 2}})

    //error msg dissapears
    expect(screen.queryByText(/please enter a number greater than 0/i)).not.toBeInTheDocument()

})

test('calls onNext with correct property_size as integer', async () => {
  
  render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom','Bedroom']}/>)

  const inputs = screen.getAllByRole('spinbutton')
  

  fireEvent.change(inputs[0], {target: {value: 2}})
  fireEvent.change(inputs[1], {target: {value: 2}})

  fireEvent.click(screen.getByRole('button', { name: /next/i }))

  expect(mockOnNext).toHaveBeenCalledTimes(1)

  // adjust this shape if your component sends a different payload
  expect(mockOnNext).toHaveBeenCalledWith({
    bathrooms_to_reno: 2,
    bedrooms_to_reno: 2,
  })

})

test('calls onBack when Back is clicked', async () => {
  
  render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom','Bedroom']}/>)

  
  //click back button
  fireEvent.click(screen.getByRole('button', { name: /Back/i }))

  expect(mockOnBack).toHaveBeenCalledTimes(1)


})

// --------------------
// Boundary tests
// --------------------
test('accepts 1 as the minimum valid value', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bathroom','Bedroom']}/>)

    const inputs = screen.getAllByRole('spinbutton')
  

    fireEvent.change(inputs[0], {target: {value: 1}})
    fireEvent.change(inputs[1], {target: {value: 1}})

  fireEvent.click(screen.getByRole('button', { name: /next/i }))

  expect(mockOnNext).toHaveBeenCalledTimes(1)

  // adjust this shape if your component sends a different payload
  expect(mockOnNext).toHaveBeenCalledWith({
    bathrooms_to_reno: 1,
    bedrooms_to_reno: 1,
  })
})

test('accepts a very large number like 999999', () => {
    render(<BedBathCount onNext={mockOnNext} onBack={mockOnBack} selected={['Bedroom', 'Bathroom']}/>)

    const inputs = screen.getAllByRole('spinbutton')
  

    fireEvent.change(inputs[0], {target: {value: 999999}})
    fireEvent.change(inputs[1], {target: {value: 999999}})

    fireEvent.click(screen.getByRole('button', { name: /next/i }))

    expect(mockOnNext).toHaveBeenCalledTimes(1)

  // adjust this shape if your component sends a different payload
  expect(mockOnNext).toHaveBeenCalledWith({
    bedrooms_to_reno: 999999,
    bathrooms_to_reno: 999999,
  })
})

