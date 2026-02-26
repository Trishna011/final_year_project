import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import React from "react"
import Location from "../components/LocationLocal"

const mockOnNext = jest.fn()
const mockOnBack = jest.fn()

beforeEach(() => {
  jest.clearAllMocks()
})

// ============================================================
// SECTION 1: Basic Rendering Tests
// Verifies the component mounts and core UI elements are present
// ============================================================

test("renders the heading", () => {
  const answers = { renovation_type: ["Kitchen"] }

  render(<Location onNext={mockOnNext} onBack={mockOnBack}vanswers={answers}/>)

  expect(
    screen.getByText(/Where is your property\?/i)
  ).toBeInTheDocument()
})

test('renders the Next button', () => {
  const answers = { renovation_type: ["Kitchen"] }

  render(<Location onNext={mockOnNext} onBack={mockOnBack}vanswers={answers}/>)

  expect(screen.getByRole('button', { name: /Next/i })).toBeInTheDocument()
})

test('renders the Back button', () => {
  const answers = { renovation_type: ["Kitchen"] }

  render(<Location onNext={mockOnNext} onBack={mockOnBack}vanswers={answers}/>)


  expect(screen.getByRole('button', { name: /Back/i })).toBeInTheDocument()
})

test("renders location dropdown with placeholder", () => {
  const answers = { renovation_type: ["Kitchen"] }

  render(<Location onNext={mockOnNext} onBack={mockOnBack}vanswers={answers}/>)

  const selectElement = screen.getByRole("combobox")
  expect(selectElement).toBeInTheDocument()

  //check default placeholder option
  expect(
    screen.getByText(/Select a location/i)
  ).toBeInTheDocument()

})

// ============================================================
// Validation tests
// ============================================================

test("when a location is selected, it shows as the selected value", () => {
  const answers = { renovation_type: ["Kitchen"] }

  render(<Location onNext={mockOnNext} onBack={mockOnBack}vanswers={answers}/>)

  const selectElement = screen.getByRole("combobox")

  fireEvent.change(selectElement, {
    target: { value: "Manchester City Centre" },
  })

  expect(selectElement.value).toBe("Manchester City Centre")
})

// ============================================================
// Negative tests
// ============================================================

test("does not call onNext when no location is selected", () => {
  const answers = { renovation_type: ["Kitchen"] }

  render(<Location onNext={mockOnNext} onBack={mockOnBack}vanswers={answers}/>)


  const nextButton = screen.getByRole("button", { name: /next/i })

  fireEvent.click(nextButton)

  expect(mockOnNext).not.toHaveBeenCalled()
})

// ============================================================
// Error message tests
// ============================================================

test("shows error message when no location is selected and Next is clicked", () => {
  const answers = { renovation_type: ["Kitchen"] }

  render(<Location onNext={mockOnNext} onBack={mockOnBack}vanswers={answers}/>)

  const nextButton = screen.getByRole("button", { name: /next/i })

  fireEvent.click(nextButton)

  expect(
    screen.getByText(/Please select a location/i)
  ).toBeInTheDocument()

  expect(mockOnNext).not.toHaveBeenCalled()
})

test("error message disappears when a valid location is selected", () => {
  const answers = { renovation_type: ["Kitchen"] }

  render(<Location onNext={mockOnNext} onBack={mockOnBack}vanswers={answers}/>)

  const nextButton = screen.getByRole("button", { name: /next/i })

  //trigger error
  fireEvent.click(nextButton)

  expect(
    screen.getByText(/Please select a location/i)
  ).toBeInTheDocument()

  //select valid location
  const selectElement = screen.getByRole("combobox")

  fireEvent.change(selectElement, {
    target: { value: "Manchester City Centre" },
  })

  expect(
    screen.queryByText(/Please select a location/i)
  ).not.toBeInTheDocument()
})

// ============================================================
// Callback Tests
// ============================================================

test("calls onNext with valid location selected", async () => {
  const answers = { renovation_type: ["Kitchen"] }

  global.fetch = jest.fn()
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        total_predicted_cost: 10000,
      }),
    })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        post_renovation_value: 250000,
      }),
    })

  render(
    <Location
      onNext={mockOnNext}
      onBack={mockOnBack}
      answers={answers}
    />
  )

  const selectElement = screen.getByRole("combobox")

  fireEvent.change(selectElement, {
    target: { value: "Manchester City Centre" },
  })

  fireEvent.click(screen.getByRole("button", { name: /next/i }))

  await waitFor(() => {
    expect(mockOnNext).toHaveBeenCalledTimes(1)
  })

  expect(mockOnNext).toHaveBeenCalledWith({
    renovation_type: ["Kitchen"],
    Location: "Manchester City Centre",
    cost: 10000,
    postRenovationValue: 250000,
  })
})

test('calls onBack when Back is clicked', async () => {
  
  const answers = { renovation_type: ["Kitchen"] }

  render(<Location onNext={mockOnNext} onBack={mockOnBack}vanswers={answers}/>)

  
  //click back button
  fireEvent.click(screen.getByRole('button', { name: /Back/i }))

  expect(mockOnBack).toHaveBeenCalledTimes(1)


})

// ============================================================
// reno cost API returns non-ok response
// ============================================================
test("calls onNext with zero values if estimate API fails", async () => {
  const answers = { renovation_type: ["Kitchen"] }

  global.fetch = jest.fn()
    .mockResolvedValueOnce({
      ok: false,
      json: async () => ({ error: "Prediction failed" }),
    })

  render(
    <Location
      onNext={mockOnNext}
      onBack={mockOnBack}
      answers={answers}
    />
  )

  fireEvent.change(screen.getByRole("combobox"), {
    target: { value: "Manchester City Centre" },
  })

  fireEvent.click(screen.getByRole("button", { name: /next/i }))

  await waitFor(() => {
    expect(mockOnNext).toHaveBeenCalledTimes(1)
  })

  expect(mockOnNext).toHaveBeenCalledWith({
    renovation_type: ["Kitchen"],
    Location: "Manchester City Centre",
    cost: 0,
    postRenovationValue: 0,
  })
})

// ============================================================
// post reno preds API fails after first succeeds
// ============================================================

test("calls onNext with zero values if value API fails", async () => {
  const answers = { renovation_type: ["Kitchen"] }

  global.fetch = jest.fn()
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        total_predicted_cost: 15000,
      }),
    })
    .mockResolvedValueOnce({
      ok: false,
      json: async () => ({ error: "Value failed" }),
    })

  render(
    <Location
      onNext={mockOnNext}
      onBack={mockOnBack}
      answers={answers}
    />
  )

  fireEvent.change(screen.getByRole("combobox"), {
    target: { value: "Manchester City Centre" },
  })

  fireEvent.click(screen.getByRole("button", { name: /next/i }))

  await waitFor(() => {
    expect(mockOnNext).toHaveBeenCalledTimes(1)
  })

  expect(mockOnNext).toHaveBeenCalledWith({
    renovation_type: ["Kitchen"],
    Location: "Manchester City Centre",
    cost: 0,
    postRenovationValue: 0,
  })
})

// ============================================================
// Network failure during reno cost API call
// ============================================================

test("calls onNext with zero values if network error occurs", async () => {
  const answers = { renovation_type: ["Kitchen"] }

  global.fetch = jest.fn().mockRejectedValue(new Error("Network error"))

  render(
    <Location
      onNext={mockOnNext}
      onBack={mockOnBack}
      answers={answers}
    />
  )

  fireEvent.change(screen.getByRole("combobox"), {
    target: { value: "Manchester City Centre" },
  })

  fireEvent.click(screen.getByRole("button", { name: /next/i }))

  await waitFor(() => {
    expect(mockOnNext).toHaveBeenCalledTimes(1)
  })

  expect(mockOnNext).toHaveBeenCalledWith({
    renovation_type: ["Kitchen"],
    Location: "Manchester City Centre",
    cost: 0,
    postRenovationValue: 0,
  })
})

// ============================================================
// Ensure correct payload sent to reno cost API
// ============================================================

test("sends correct payload to estimate API", async () => {
  const answers = { renovation_type: ["Kitchen"] }

  global.fetch = jest.fn()
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        total_predicted_cost: 12000,
      }),
    })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        post_renovation_value: 240000,
      }),
    })

  render(
    <Location
      onNext={mockOnNext}
      onBack={mockOnBack}
      answers={answers}
    />
  )

  fireEvent.change(screen.getByRole("combobox"), {
    target: { value: "Salford" },
  })

  fireEvent.click(screen.getByRole("button", { name: /next/i }))

  await waitFor(() => {
    expect(global.fetch).toHaveBeenCalled()
  })

  expect(global.fetch).toHaveBeenNthCalledWith(
    1,
    "http://localhost:4000/api/estimate",
    expect.objectContaining({
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        renovation_type: ["Kitchen"],
        Location: "Salford",
      }),
    })
  )
})