import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import React from "react"
import CostPage from "../components/CostPage"

const mockOnRestart = jest.fn()
const mockClearAnswers = jest.fn()

beforeEach(() => {
  jest.clearAllMocks()
})

// ============================================================
// SECTION 1: Basic Rendering Tests
// ============================================================

test("renders renovation cost heading", () => {
  render(
    <CostPage
      cost={15000}
      postRenovationValue={250000}
      onRestart={mockOnRestart}
      clearAnswers={mockClearAnswers}
    />
  )

  expect(
    screen.getByText(/Your Estimated Renovation Cost/i)
  ).toBeInTheDocument()
})

test("renders post renovation value heading", () => {
  render(
    <CostPage
      cost={15000}
      postRenovationValue={250000}
      onRestart={mockOnRestart}
      clearAnswers={mockClearAnswers}
    />
  )

  expect(
    screen.getByText(/Estimated Property Value After Renovation/i)
  ).toBeInTheDocument()
})

test("renders Start Over button", () => {
  render(
    <CostPage
      cost={15000}
      postRenovationValue={250000}
      onRestart={mockOnRestart}
      clearAnswers={mockClearAnswers}
    />
  )

  expect(
    screen.getByRole("button", { name: /Start Over/i })
  ).toBeInTheDocument()
})


// ============================================================
// Value Rendering Tests
// ============================================================
test("formats renovation cost correctly", () => {
  render(
    <CostPage
      cost={15000}
      postRenovationValue={250000}
      onRestart={mockOnRestart}
      clearAnswers={mockClearAnswers}
    />
  )

  expect(screen.getByText("£15,000")).toBeInTheDocument()
})

test("formats post renovation value correctly", () => {
  render(
    <CostPage
      cost={15000}
      postRenovationValue={250000}
      onRestart={mockOnRestart}
      clearAnswers={mockClearAnswers}
    />
  )

  expect(screen.getByText("£250,000")).toBeInTheDocument()
})

test("defaults cost to £0 when undefined", () => {
  render(
    <CostPage
      cost={undefined}
      postRenovationValue={250000}
      onRestart={mockOnRestart}
      clearAnswers={mockClearAnswers}
    />
  )

  expect(screen.getByText("£0")).toBeInTheDocument()
})

test("defaults post renovation value to £0 when undefined", () => {
  render(
    <CostPage
      cost={15000}
      postRenovationValue={undefined}
      onRestart={mockOnRestart}
      clearAnswers={mockClearAnswers}
    />
  )

  expect(screen.getByText("£0")).toBeInTheDocument()
})

// ============================================================
// Edge Case Tests
// ============================================================
test("handles zero values correctly", () => {
  render(
    <CostPage
      cost={0}
      postRenovationValue={0}
      onRestart={mockOnRestart}
      clearAnswers={mockClearAnswers}
    />
  )

  const zeroValues = screen.getAllByText("£0")
  expect(zeroValues.length).toBe(2)
})

test("handles large numbers correctly", () => {
  render(
    <CostPage
      cost={1250000}
      postRenovationValue={2500000}
      onRestart={mockOnRestart}
      clearAnswers={mockClearAnswers}
    />
  )

  expect(screen.getByText("£1,250,000")).toBeInTheDocument()
  expect(screen.getByText("£2,500,000")).toBeInTheDocument()
})

// ============================================================
// Callback Tests
// ============================================================
test("calls clearAnswers and onRestart when Start Over is clicked", () => {
  render(
    <CostPage
      cost={15000}
      postRenovationValue={250000}
      onRestart={mockOnRestart}
      clearAnswers={mockClearAnswers}
    />
  )

  fireEvent.click(screen.getByRole("button", { name: /Start Over/i }))

  expect(mockClearAnswers).toHaveBeenCalledTimes(1)
  expect(mockOnRestart).toHaveBeenCalledTimes(1)
})
