/**
 * App.integration.test.js
 * Integration tests for the Property Renovation Calculator.
 *
 * ─── What makes these integration tests (not unit tests) ────────────────────
 * Unlike the unit tests in App.test.js, these tests render the REAL child
 * components with NO mocking of any component. The full React tree — App,
 * RenoType, BedBathCount, SqftToAdd, StructChanges, SqftToReno, MaterialGrade,
 * PropertySize, Location_local, CostPage — is mounted together.
 *
 * This means:
 *   • Real component state drives each step, not mock callbacks
 *   • Real prop passing between App and children is exercised
 *   • Real validation logic inside each child blocks or permits step transitions
 *   • The answers object that App accumulates is the product of real onNext calls
 *
 * ─── What is still mocked ───────────────────────────────────────────────────
 * Only two things are mocked:
 *   1. framer-motion — because jsdom cannot run CSS animations
 *   2. global.fetch   — because Location_local.js calls a real HTTP server;
 *                       we control the response to keep tests deterministic
 *
 * ─── The three journeys tested ──────────────────────────────────────────────
 * Test 1 — "Kitchen-only non-branching flow"
 *   Selects Kitchen → skips BedBathCount → completes all remaining steps →
 *   reaches CostPage showing the mocked cost. Verifies the non-branching path
 *   works end-to-end and that the cost returned by the API is displayed.
 *
 * Test 2 — "Bedroom+Bathroom branching flow with BedBathCount"
 *   Selects Bedroom + Bathroom → enters BedBathCount (step 2) → completes all
 *   steps → verifies that the bedroom/bathroom count from BedBathCount is
 *   correctly propagated into SqftToAdd (which renders per-room inputs).
 *
 * Test 3 — "Validation gates prevent progression and can be cleared"
 *   Attempts to advance past RenoType, SqftToAdd, and PropertySize without
 *   filling in the required fields, verifies error messages appear, then fills
 *   them in and confirms progression is unblocked.
 */

import React from 'react'
import { render, screen, fireEvent, waitFor, within, act } from '@testing-library/react'
import App from '../App'

// ─── Stub framer-motion ───────────────────────────────────────────────────────
// jsdom has no layout engine so animation transforms are meaningless.
// We strip animation props and render the underlying HTML element directly.
jest.mock('framer-motion', () => {
  const React = require('react')
  const motion = (Tag) =>
    React.forwardRef(({ initial, animate, exit, transition, whileHover, whileTap, ...rest }, ref) => (
      <Tag ref={ref} {...rest} />
    ))
  return {
    motion,
    AnimatePresence: ({ children }) => <>{children}</>,
  }
})

// ─── Helpers ──────────────────────────────────────────────────────────────────

/** Click the Start Here button on the LandingPage. */
function clickStart() {
  fireEvent.click(screen.getByRole('button', { name: /Start Here/i }))
}

/** Click the labelled Next button. */
function clickNext() {
  fireEvent.click(screen.getByRole('button', { name: /^Next$/i }))
}

/** Click the labelled Back button. */
function clickBack() {
  fireEvent.click(screen.getByRole('button', { name: /^Back$/i }))
}

/**
 * Complete the SqftToAdd step (step 3).
 * Fills in all visible textboxes with the given value (default "0").
 */
function fillSqftToAdd(value = '0') {
  screen.getAllByRole('textbox').forEach((input) => {
    fireEvent.change(input, { target: { value } })
  })
  clickNext()
}

/**
 * Complete the StructChanges step (step 4).
 * Clicks the first available "No" option for every room card.
 */
function fillStructChanges() {
  // Each room card has a Yes/No pair — click the first "No" in every card
  const noButtons = screen.getAllByText('No')
  noButtons.forEach((btn) => fireEvent.click(btn))
  clickNext()
}

/**
 * Complete the SqftToReno step (step 5).
 * Fills all textboxes with the given value.
 */
function fillSqftToReno(value = '100') {
  screen.getAllByRole('textbox').forEach((input) => {
    fireEvent.change(input, { target: { value } })
  })
  clickNext()
}

/**
 * Complete the MaterialGrade step (step 6).
 * Selects "Mid-range" from every visible material dropdown.
 */
function fillMaterialGrade() {
  // Each room has a <select> dropdown — select Mid-range for all
  const selects = screen.getAllByRole('combobox')
  selects.forEach((select) => {
    fireEvent.change(select, { target: { value: 'Mid-range' } })
  })
  clickNext()
}

/**
 * Complete the PropertySize step (step 7).
 */
function fillPropertySize(value = '1000') {
  fireEvent.change(screen.getByRole('textbox'), { target: { value } })
  clickNext()
}

/**
 * Complete the Location step (step 8).
 * Selects the given location from the dropdown and clicks Next.
 * fetch must already be mocked before calling this.
 */
async function fillLocationAndWait(location = 'Salford') {
  // There are two comboboxes on this step if MaterialGrade is already gone —
  // the location step has exactly one combobox
  fireEvent.change(screen.getByRole('combobox'), { target: { value: location } })
  clickNext()
  // Wait for the async fetch to resolve and CostPage to appear
  await waitFor(() =>
    expect(screen.getByText(/Your Estimated Renovation Cost/i)).toBeInTheDocument()
  )
}

/** Build a successful fetch mock returning a cost and post-renovation value. */
function mockFetchSuccess(cost = 25000, postValue = 350000) {
  global.fetch = jest.fn()
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({ total_predicted_cost: cost }),
    })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({ post_renovation_value: postValue }),
    })
}

beforeEach(() => {
  jest.clearAllMocks()
  jest.useFakeTimers()
})

afterEach(() => {
  act(() => { jest.runOnlyPendingTimers() })
  jest.useRealTimers()
  delete global.fetch
})

// ══════════════════════════════════════════════════════════════════════════════
// INTEGRATION TEST 1
// Journey: Kitchen-only → skip BedBathCount → complete all steps → CostPage
//
// This test verifies that:
//   • Selecting a non-bedroom/bathroom type skips step 2 (BedBathCount) entirely
//   • Each step correctly receives the accumulated answers from App
//   • The API cost returned by Location_local is passed through to CostPage
//   • CostPage renders the formatted cost that came from the API
// ══════════════════════════════════════════════════════════════════════════════

test('Integration 1: Kitchen-only flow completes all steps and displays API cost on CostPage', async () => {
  mockFetchSuccess(42000, 310000)
  render(<App />)

  // ── Landing Page ──────────────────────────────────────────────────────────
  expect(screen.getByText(/Property Renovation Calculator/i)).toBeInTheDocument()
  clickStart()

  // ── Step 1: RenoType ──────────────────────────────────────────────────────
  expect(screen.getByText(/What would you like to renovate\?/i)).toBeInTheDocument()
  // Select Kitchen only — should NOT trigger BedBathCount
  fireEvent.click(screen.getByText('Kitchen'))
  clickNext()

  // ── Step 2 should be SKIPPED — SqftToAdd (step 3) appears directly ────────
  expect(screen.getByText(/Are you doing an extension\?/i)).toBeInTheDocument()
  expect(screen.queryByText(/How many rooms\?/i)).not.toBeInTheDocument()
  // Progress bar confirms we are at step 3
  expect(screen.getByText('Step 3 of 9')).toBeInTheDocument()

  // ── Step 3: SqftToAdd ─────────────────────────────────────────────────────
  // Kitchen input should be visible (one textbox for the Kitchen room)
  expect(screen.getByText('Kitchen')).toBeInTheDocument()
  fillSqftToAdd('50')

  // ── Step 4: StructChanges ─────────────────────────────────────────────────
  expect(screen.getByText(/Any structural changes required\?/i)).toBeInTheDocument()
  // Kitchen room card should be present (not bedroom/bathroom cards)
  expect(screen.getByText('Kitchen')).toBeInTheDocument()
  fillStructChanges()

  // ── Step 5: SqftToReno ────────────────────────────────────────────────────
  expect(screen.getByText(/Sqft to Renovate/i)).toBeInTheDocument()
  fillSqftToReno('200')

  // ── Step 6: MaterialGrade ─────────────────────────────────────────────────
  expect(screen.getByText(/Select Material Grade/i)).toBeInTheDocument()
  fillMaterialGrade()

  // ── Step 7: PropertySize ──────────────────────────────────────────────────
  expect(screen.getByText(/What is the property size\?/i)).toBeInTheDocument()
  fillPropertySize('900')

  // ── Step 8: Location ──────────────────────────────────────────────────────
  expect(screen.getByText(/Where is your property\?/i)).toBeInTheDocument()
  await fillLocationAndWait('Salford')

  // ── Step 9: CostPage ──────────────────────────────────────────────────────
  // The API returned 42000 — CostPage should display £42,000
  expect(screen.getByText('£42,000')).toBeInTheDocument()
  // Post renovation value should also be displayed
  expect(screen.getByText('£310,000')).toBeInTheDocument()
  // Start Over button is present
  expect(screen.getByRole('button', { name: /Start Over/i })).toBeInTheDocument()
})

// ══════════════════════════════════════════════════════════════════════════════
// INTEGRATION TEST 2
// Journey: Bedroom + Bathroom → BedBathCount (2 beds, 1 bath) → SqftToAdd
//          shows 3 individual room inputs → complete all steps → CostPage
//
// This test verifies that:
//   • Selecting Bedroom + Bathroom routes through step 2 (BedBathCount)
//   • The bedrooms_to_reno and bathrooms_to_reno values set in BedBathCount
//     are correctly passed through App's answers state to SqftToAdd
//   • SqftToAdd renders the correct number of per-room inputs (2 beds + 1 bath)
//     proving that App's accumulated answers object is correctly threaded
//     through as props — something unit tests with mocks cannot verify
// ══════════════════════════════════════════════════════════════════════════════

test('Integration 2: Bedroom+Bathroom flow passes room counts through BedBathCount into SqftToAdd', async () => {
  mockFetchSuccess(55000, 420000)
  render(<App />)

  clickStart()

  // ── Step 1: RenoType — select Bedroom AND Bathroom ────────────────────────
  expect(screen.getByText(/What would you like to renovate\?/i)).toBeInTheDocument()
  fireEvent.click(screen.getByText('Bedroom'))
  fireEvent.click(screen.getByText('Bathroom'))
  clickNext()

  // ── Step 2: BedBathCount — MUST appear ────────────────────────────────────
  expect(screen.getByText(/How many rooms\?/i)).toBeInTheDocument()
  expect(screen.getByText('Step 2 of 9')).toBeInTheDocument()

  // Set 2 bedrooms and 1 bathroom using the number inputs
  const [bedroomInput, bathroomInput] = screen.getAllByRole('spinbutton')
  fireEvent.change(bedroomInput, { target: { value: '2' } })
  fireEvent.change(bathroomInput, { target: { value: '1' } })
  clickNext()

  // ── Step 3: SqftToAdd — must show 3 separate room cards ──────────────────
  expect(screen.getByText(/Are you doing an extension\?/i)).toBeInTheDocument()
  expect(screen.getByText('Step 3 of 9')).toBeInTheDocument()

  // Bedroom 1 and Bedroom 2 cards must appear (from bedrooms_to_reno: 2)
  expect(screen.getByText('Bedroom 1')).toBeInTheDocument()
  expect(screen.getByText('Bedroom 2')).toBeInTheDocument()
  // Bathroom 1 card must appear (from bathrooms_to_reno: 1)
  expect(screen.getByText('Bathroom 1')).toBeInTheDocument()
  // There should be exactly 3 textbox inputs (one per room)
  expect(screen.getAllByRole('textbox')).toHaveLength(3)

  // Fill all 3 inputs and continue
  fillSqftToAdd('0')

  // ── Step 4: StructChanges — should show 3 room cards ─────────────────────
  expect(screen.getByText(/Any structural changes required\?/i)).toBeInTheDocument()
  expect(screen.getByText('Bedroom 1')).toBeInTheDocument()
  expect(screen.getByText('Bedroom 2')).toBeInTheDocument()
  expect(screen.getByText('Bathroom 1')).toBeInTheDocument()
  fillStructChanges()

  // ── Step 5: SqftToReno ────────────────────────────────────────────────────
  expect(screen.getByText(/Sqft to Renovate/i)).toBeInTheDocument()
  fillSqftToReno('150')

  // ── Step 6: MaterialGrade ─────────────────────────────────────────────────
  expect(screen.getByText(/Select Material Grade/i)).toBeInTheDocument()
  fillMaterialGrade()

  // ── Step 7: PropertySize ──────────────────────────────────────────────────
  fillPropertySize('1200')

  // ── Step 8: Location ──────────────────────────────────────────────────────
  await fillLocationAndWait('Manchester City Centre')

  // ── Step 9: CostPage ──────────────────────────────────────────────────────
  expect(screen.getByText('£55,000')).toBeInTheDocument()
  expect(screen.getByText('£420,000')).toBeInTheDocument()
})

// ══════════════════════════════════════════════════════════════════════════════
// INTEGRATION TEST 3
// Journey: Validation gates across multiple steps block progression,
//          show correct error messages, and clear once input is provided.
//
// This test verifies that:
//   • RenoType blocks Next and shows "Please select at least one option"
//     when nothing is selected
//   • SqftToAdd blocks Next and shows "Please fill in all fields before
//     continuing" when an input is left empty
//   • PropertySize blocks Next with "Please enter a value" when empty,
//     and "Please enter a number greater than 0" when 0 is entered
//   • In all cases, providing valid input clears the error and unblocks
//     progression — confirming the error/clear cycle works end-to-end
//     across the real component + real App state boundary
// ══════════════════════════════════════════════════════════════════════════════

test('Integration 3: Validation gates block progression and clear correctly across multiple steps', async () => {
  mockFetchSuccess(18000, 280000)
  render(<App />)

  clickStart()

  // ── Step 1: RenoType — clicking Next with nothing selected shows error ─────
  expect(screen.getByText(/What would you like to renovate\?/i)).toBeInTheDocument()
  clickNext()
  expect(screen.getByText(/Please select at least one option/i)).toBeInTheDocument()
  // Still on step 1
  expect(screen.getByText('Step 1 of 9')).toBeInTheDocument()

  // Selecting an option clears the error immediately (before clicking Next)
  fireEvent.click(screen.getByText('Kitchen'))
  expect(screen.queryByText(/Please select at least one option/i)).not.toBeInTheDocument()

  // Now Next proceeds to step 3 (Kitchen skips BedBathCount)
  clickNext()
  expect(screen.getByText(/Are you doing an extension\?/i)).toBeInTheDocument()

  // ── Step 3: SqftToAdd — clicking Next with empty input shows error ─────────
  // The Kitchen input starts empty — click Next without filling it
  clickNext()
  expect(screen.getByText(/Please fill in all fields before continuing/i)).toBeInTheDocument()
  // Still on step 3
  expect(screen.getByText('Step 3 of 9')).toBeInTheDocument()

  // Fill the input — error should clear and Next should work
  fireEvent.change(screen.getByRole('textbox'), { target: { value: '0' } })
  expect(screen.queryByText(/Please fill in all fields before continuing/i)).not.toBeInTheDocument()
  clickNext()
  expect(screen.getByText(/Any structural changes required\?/i)).toBeInTheDocument()

  // ── Step 4: StructChanges ─────────────────────────────────────────────────
  fillStructChanges()

  // ── Step 5: SqftToReno ────────────────────────────────────────────────────
  // Clicking Next with empty input shows error
  clickNext()
  expect(screen.getByText(/Please fill in all fields before continuing/i)).toBeInTheDocument()
  expect(screen.getByText('Step 5 of 9')).toBeInTheDocument()
  // Fill and continue
  fireEvent.change(screen.getByRole('textbox'), { target: { value: '100' } })
  clickNext()
  expect(screen.getByText(/Select Material Grade/i)).toBeInTheDocument()

  // ── Step 6: MaterialGrade ─────────────────────────────────────────────────
  // Clicking Next without selecting a grade shows error
  clickNext()
  expect(screen.getByText(/Please select a material grade for all rooms/i)).toBeInTheDocument()
  expect(screen.getByText('Step 6 of 9')).toBeInTheDocument()
  // Select grade and continue
  fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Budget-friendly' } })
  clickNext()
  expect(screen.getByText(/What is the property size\?/i)).toBeInTheDocument()

  // ── Step 7: PropertySize — two distinct error messages ────────────────────
  // Empty input → "Please enter a value"
  clickNext()
  expect(screen.getByText(/Please enter a value/i)).toBeInTheDocument()
  expect(screen.getByText('Step 7 of 9')).toBeInTheDocument()

  // Zero input → "Please enter a number greater than 0"
  fireEvent.change(screen.getByRole('textbox'), { target: { value: '0' } })
  clickNext()
  expect(screen.getByText(/Please enter a number greater than 0/i)).toBeInTheDocument()

  // Valid input clears error and proceeds
  fireEvent.change(screen.getByRole('textbox'), { target: { value: '800' } })
  expect(screen.queryByText(/Please enter a number greater than 0/i)).not.toBeInTheDocument()
  clickNext()
  expect(screen.getByText(/Where is your property\?/i)).toBeInTheDocument()

  // ── Step 8: Location — clicking Next without selection shows error ─────────
  clickNext()
  expect(screen.getByText(/Please select a location/i)).toBeInTheDocument()
  expect(screen.getByText('Step 8 of 9')).toBeInTheDocument()

  // Select a location — error clears
  fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Didsbury' } })
  expect(screen.queryByText(/Please select a location/i)).not.toBeInTheDocument()

  // Submit and reach CostPage
  clickNext()
  await waitFor(() =>
    expect(screen.getByText(/Your Estimated Renovation Cost/i)).toBeInTheDocument()
  )
  expect(screen.getByText('£18,000')).toBeInTheDocument()
})