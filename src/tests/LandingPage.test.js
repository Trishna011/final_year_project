import { render, screen, fireEvent } from '@testing-library/react'
import React from "react"
import LandingPage from "../components/LandingPage"

const mockOnStart = jest.fn()

//reset mocks before each test
beforeEach(() => {
  jest.clearAllMocks()
})

// ============================================================
// SECTION 1: Basic Rendering Tests
// ============================================================

test("renders the heading text", () => {
  render(<LandingPage onStart={mockOnStart} />)

  expect(
    screen.getByText(/Property Renovation Calculator/i)
  ).toBeInTheDocument()
})

test("renders the Start button", () => {
  render(<LandingPage onStart={mockOnStart} />)

  expect(
    screen.getByRole("button", { name: /Start Here/i })
  ).toBeInTheDocument()
})

test("Start button is enabled by default", () => {
  render(<LandingPage onStart={mockOnStart} />)

  const btn = screen.getByRole("button", { name: /Start Here/i })
  expect(btn).toBeEnabled()
})

// ============================================================
// SECTION 2: Callback Tests
// ============================================================

test("calls onStart once when Start Here is clicked", () => {
  render(<LandingPage onStart={mockOnStart} />)

  fireEvent.click(screen.getByRole("button", { name: /Start Here/i }))

  expect(mockOnStart).toHaveBeenCalledTimes(1)
})

test("calls onStart once per click", () => {
  render(<LandingPage onStart={mockOnStart} />)

  const btn = screen.getByRole("button", { name: /Start Here/i })

  fireEvent.click(btn)
  fireEvent.click(btn)
  fireEvent.click(btn)

  expect(mockOnStart).toHaveBeenCalledTimes(3)
})

// ============================================================
// SECTION 3: Defensive and Negative Tests
// ============================================================
test("does not throw if onStart is not provided", () => {
  expect(() => render(<LandingPage />)).not.toThrow()
})


test("clicking Start Here does not throw when onStart is missing", () => {
  render(<LandingPage />)

  const btn = screen.getByRole("button", { name: /Start Here/i })
  expect(() => fireEvent.click(btn)).not.toThrow()
})