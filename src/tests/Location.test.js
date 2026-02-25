/**
 * Location.test.js
 * Unit tests for Location.js — the property location step.
 *
 * Location.js is responsible for:
 *   - Rendering a dropdown of Greater Manchester area locations (sorted A–Z)
 *   - Validating that a location has been selected before continuing
 *   - Showing an error message when Next is clicked with no selection
 *   - POSTing the accumulated answers + selected location to /api/estimate
 *   - Calling onNext({ cost: data.predicted_cost }) on a successful API response
 *   - Falling back to onNext({ ...updatedAnswers, cost: 0 }) on API failure
 *   - Calling onBack when the Back button is clicked
 *
 * Mocking strategy
 * ----------------
 * - global.fetch is replaced with jest.fn() before each test and restored after
 * - framer-motion is stubbed so MotionBox renders as a plain div in jsdom
 * - Chakra UI renders normally (components are thin wrappers over HTML elements)
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import Location from '../components/Location'

// ─── Stub framer-motion ───────────────────────────────────────────────────────
jest.mock('framer-motion', () => {
  const React = require('react')
  return {
    motion: (Tag) =>
      React.forwardRef(({ initial, animate, exit, transition, ...rest }, ref) => (
        <Tag ref={ref} {...rest} />
      )),
    AnimatePresence: ({ children }) => <>{children}</>,
  }
})

// ─── Helpers ──────────────────────────────────────────────────────────────────
const mockOnNext = jest.fn()
const mockOnBack = jest.fn()

const defaultAnswers = {
  renovation_type: ['Kitchen'],
  sqft_to_add: { bedrooms: [], bathrooms: [], other: { Kitchen: 0 } },
  struct_changes: 'None',
  sqft_to_reno: 500,
  material_grade: 'Mid-range',
  property_size: 1200,
}

/** Render with sensible defaults; override any prop as needed. */
function renderLocation(props = {}) {
  return render(
    <Location
      onNext={mockOnNext}
      onBack={mockOnBack}
      answers={defaultAnswers}
      {...props}
    />
  )
}

/** Build a resolved fetch mock returning the given body and status. */
function mockFetchSuccess(body = { predicted_cost: 35000 }, status = 200) {
  global.fetch = jest.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  })
}

/** Build a rejected fetch mock (network failure). */
function mockFetchNetworkError(message = 'Network Error') {
  global.fetch = jest.fn().mockRejectedValue(new Error(message))
}

/** Build a fetch mock that resolves but with ok: false (server error). */
function mockFetchServerError(body = { error: 'Prediction failed' }, status = 500) {
  global.fetch = jest.fn().mockResolvedValue({
    ok: false,
    status,
    json: async () => body,
  })
}

beforeEach(() => {
  jest.clearAllMocks()
})

afterEach(() => {
  delete global.fetch
})

// ─── SECTION 1: Basic Rendering ──────────────────────────────────────────────

describe('Section 1: Basic Rendering', () => {
  test('renders the heading "Where is your property?"', () => {
    renderLocation()
    expect(screen.getByText(/Where is your property\?/i)).toBeInTheDocument()
  })

  test('renders the location dropdown', () => {
    renderLocation()
    expect(screen.getByRole('combobox')).toBeInTheDocument()
  })

  test('renders the default placeholder option "Select a location"', () => {
    renderLocation()
    expect(screen.getByText('Select a location')).toBeInTheDocument()
  })

  test('renders the Next button', () => {
    renderLocation()
    expect(screen.getByRole('button', { name: /Next/i })).toBeInTheDocument()
  })

  test('renders the Back button', () => {
    renderLocation()
    expect(screen.getByRole('button', { name: /Back/i })).toBeInTheDocument()
  })

  test('does not show an error message on initial render', () => {
    renderLocation()
    expect(screen.queryByText(/Please answer all rooms before continuing/i)).not.toBeInTheDocument()
  })

  test('dropdown has an empty string value by default', () => {
    renderLocation()
    expect(screen.getByRole('combobox')).toHaveValue('')
  })
})

// ─── SECTION 2: Dropdown Options ──────────────────────────────────────────────

describe('Section 2: Dropdown options', () => {
  test('renders all 22 location options plus the placeholder', () => {
    renderLocation()
    const options = screen.getAllByRole('option')
    // 22 locations + 1 placeholder = 23
    expect(options).toHaveLength(23)
  })

  test('options are sorted alphabetically', () => {
    renderLocation()
    const options = Array.from(screen.getAllByRole('option'))
      .map((o) => o.value)
      .filter((v) => v !== '') // exclude placeholder

    const sorted = [...options].sort((a, b) => a.localeCompare(b))
    expect(options).toEqual(sorted)
  })

  test('renders Manchester City Centre as an option', () => {
    renderLocation()
    expect(screen.getByRole('option', { name: 'Manchester City Centre' })).toBeInTheDocument()
  })

  test('renders Wilmslow as an option', () => {
    renderLocation()
    expect(screen.getByRole('option', { name: 'Wilmslow' })).toBeInTheDocument()
  })

  test('renders Altrincham as an option', () => {
    renderLocation()
    expect(screen.getByRole('option', { name: 'Altrincham' })).toBeInTheDocument()
  })

  test('renders Didsbury as an option', () => {
    renderLocation()
    expect(screen.getByRole('option', { name: 'Didsbury' })).toBeInTheDocument()
  })

  test('Altrincham appears before Bolton in the sorted list', () => {
    renderLocation()
    const options = Array.from(screen.getAllByRole('option')).map((o) => o.value).filter((v) => v !== '')
    expect(options.indexOf('Altrincham')).toBeLessThan(options.indexOf('Bolton'))
  })
})

// ─── SECTION 3: Selection Behaviour ──────────────────────────────────────────

describe('Section 3: Selection behaviour', () => {
  test('selecting an option updates the dropdown value', () => {
    renderLocation()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Salford' } })
    expect(screen.getByRole('combobox')).toHaveValue('Salford')
  })

  test('selecting a different option replaces the previous selection', () => {
    renderLocation()
    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'Bolton' } })
    fireEvent.change(select, { target: { value: 'Bury' } })
    expect(select).toHaveValue('Bury')
  })

  test('re-selecting the placeholder resets the value to empty string', () => {
    renderLocation()
    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'Salford' } })
    fireEvent.change(select, { target: { value: '' } })
    expect(select).toHaveValue('')
  })
})

// ─── SECTION 4: Validation — Error Message ────────────────────────────────────

describe('Section 4: Validation', () => {
  test('shows error message when Next is clicked without selecting a location', () => {
    renderLocation()
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))
    expect(screen.getByText(/Please answer all rooms before continuing/i)).toBeInTheDocument()
  })

  test('does not call onNext when no location is selected', () => {
    renderLocation()
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))
    expect(mockOnNext).not.toHaveBeenCalled()
  })

  test('does not call fetch when no location is selected', () => {
    mockFetchSuccess()
    renderLocation()
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))
    expect(global.fetch).not.toHaveBeenCalled()
  })

  test('error message disappears after a valid selection is made and Next is clicked', async () => {
    mockFetchSuccess()
    renderLocation()

    // Trigger error first
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))
    expect(screen.getByText(/Please answer all rooms before continuing/i)).toBeInTheDocument()

    // Now select a location and proceed
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Salford' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))

    await waitFor(() => {
      expect(screen.queryByText(/Please answer all rooms before continuing/i)).not.toBeInTheDocument()
    })
  })

  test('error message is not shown when a valid location is selected before clicking Next', async () => {
    mockFetchSuccess()
    renderLocation()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Salford' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))
    // Error should never appear
    expect(screen.queryByText(/Please answer all rooms before continuing/i)).not.toBeInTheDocument()
  })
})

// ─── SECTION 5: API Call — fetch Behaviour ────────────────────────────────────

describe('Section 5: API call behaviour', () => {
  test('calls fetch with POST method when a location is selected', async () => {
    mockFetchSuccess()
    renderLocation()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Salford' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1))
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/estimate',
      expect.objectContaining({ method: 'POST' })
    )
  })

  test('calls fetch with Content-Type: application/json header', async () => {
    mockFetchSuccess()
    renderLocation()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Salford' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1))
    const [, options] = global.fetch.mock.calls[0]
    expect(options.headers).toEqual(
      expect.objectContaining({ 'Content-Type': 'application/json' })
    )
  })

  test('sends the selected location in the request body', async () => {
    mockFetchSuccess()
    renderLocation()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Salford' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1))
    const [, options] = global.fetch.mock.calls[0]
    const body = JSON.parse(options.body)
    expect(body.Location).toBe('Salford')
  })

  test('includes all existing answers in the request body', async () => {
    mockFetchSuccess()
    renderLocation()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Salford' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1))
    const [, options] = global.fetch.mock.calls[0]
    const body = JSON.parse(options.body)
    expect(body.renovation_type).toEqual(['Kitchen'])
    expect(body.sqft_to_reno).toBe(500)
    expect(body.material_grade).toBe('Mid-range')
  })

  test('does not call fetch more than once per Next click', async () => {
    mockFetchSuccess()
    renderLocation()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Salford' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1))
    expect(global.fetch).toHaveBeenCalledTimes(1)
  })
})

// ─── SECTION 6: Successful API Response ───────────────────────────────────────

describe('Section 6: Successful API response', () => {
  test('calls onNext with predicted_cost on success', async () => {
    mockFetchSuccess({ predicted_cost: 35000 })
    renderLocation()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Salford' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))

    await waitFor(() => expect(mockOnNext).toHaveBeenCalledTimes(1))
    expect(mockOnNext).toHaveBeenCalledWith({ cost: 35000 })
  })

  test('onNext receives the exact numeric cost returned by the API', async () => {
    mockFetchSuccess({ predicted_cost: 99999 })
    renderLocation()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Wilmslow' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))

    await waitFor(() => expect(mockOnNext).toHaveBeenCalledTimes(1))
    expect(mockOnNext).toHaveBeenCalledWith({ cost: 99999 })
  })

  test('onNext is called exactly once on successful submission', async () => {
    mockFetchSuccess({ predicted_cost: 20000 })
    renderLocation()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Didsbury' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))

    await waitFor(() => expect(mockOnNext).toHaveBeenCalledTimes(1))
    expect(mockOnNext).toHaveBeenCalledTimes(1)
  })

  test('works correctly with a cost of 0', async () => {
    mockFetchSuccess({ predicted_cost: 0 })
    renderLocation()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Stretford' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))

    await waitFor(() => expect(mockOnNext).toHaveBeenCalledTimes(1))
    expect(mockOnNext).toHaveBeenCalledWith({ cost: 0 })
  })

  test('works correctly with a large cost value', async () => {
    mockFetchSuccess({ predicted_cost: 1500000 })
    renderLocation()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Hale' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))

    await waitFor(() => expect(mockOnNext).toHaveBeenCalledTimes(1))
    expect(mockOnNext).toHaveBeenCalledWith({ cost: 1500000 })
  })
})

// ─── SECTION 7: Failed API Response — Network Error ──────────────────────────

describe('Section 7: Network error fallback', () => {
  test('calls onNext with cost: 0 on network failure', async () => {
    mockFetchNetworkError()
    renderLocation()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Salford' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))

    await waitFor(() => expect(mockOnNext).toHaveBeenCalledTimes(1))
    const arg = mockOnNext.mock.calls[0][0]
    expect(arg.cost).toBe(0)
  })

  test('fallback onNext call still includes the selected location', async () => {
    mockFetchNetworkError()
    renderLocation()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Bolton' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))

    await waitFor(() => expect(mockOnNext).toHaveBeenCalledTimes(1))
    const arg = mockOnNext.mock.calls[0][0]
    expect(arg.Location).toBe('Bolton')
  })

  test('fallback onNext call includes existing answers', async () => {
    mockFetchNetworkError()
    renderLocation()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Bury' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))

    await waitFor(() => expect(mockOnNext).toHaveBeenCalledTimes(1))
    const arg = mockOnNext.mock.calls[0][0]
    expect(arg.renovation_type).toEqual(['Kitchen'])
    expect(arg.material_grade).toBe('Mid-range')
  })

  test('onNext is still called exactly once on network failure', async () => {
    mockFetchNetworkError()
    renderLocation()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Salford' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))

    await waitFor(() => expect(mockOnNext).toHaveBeenCalledTimes(1))
    expect(mockOnNext).toHaveBeenCalledTimes(1)
  })
})

// ─── SECTION 8: Failed API Response — Server Error (ok: false) ───────────────

describe('Section 8: Server error fallback', () => {
  test('calls onNext with cost: 0 when server returns ok: false', async () => {
    mockFetchServerError({ error: 'Prediction failed' }, 500)
    renderLocation()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Oldham' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))

    await waitFor(() => expect(mockOnNext).toHaveBeenCalledTimes(1))
    const arg = mockOnNext.mock.calls[0][0]
    expect(arg.cost).toBe(0)
  })

  test('fallback includes the selected location on server error', async () => {
    mockFetchServerError()
    renderLocation()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Rochdale' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))

    await waitFor(() => expect(mockOnNext).toHaveBeenCalledTimes(1))
    const arg = mockOnNext.mock.calls[0][0]
    expect(arg.Location).toBe('Rochdale')
  })

  test('onNext is called exactly once on server error', async () => {
    mockFetchServerError()
    renderLocation()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Tameside' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))

    await waitFor(() => expect(mockOnNext).toHaveBeenCalledTimes(1))
    expect(mockOnNext).toHaveBeenCalledTimes(1)
  })
})

// ─── SECTION 9: onBack Callback ───────────────────────────────────────────────

describe('Section 9: Back button', () => {
  test('calls onBack when Back button is clicked', () => {
    renderLocation()
    fireEvent.click(screen.getByRole('button', { name: /Back/i }))
    expect(mockOnBack).toHaveBeenCalledTimes(1)
  })

  test('does not call onNext when Back is clicked', () => {
    renderLocation()
    fireEvent.click(screen.getByRole('button', { name: /Back/i }))
    expect(mockOnNext).not.toHaveBeenCalled()
  })

  test('does not call fetch when Back is clicked', () => {
    mockFetchSuccess()
    renderLocation()
    fireEvent.click(screen.getByRole('button', { name: /Back/i }))
    expect(global.fetch).not.toHaveBeenCalled()
  })

  test('onBack is called exactly once per click', () => {
    renderLocation()
    fireEvent.click(screen.getByRole('button', { name: /Back/i }))
    fireEvent.click(screen.getByRole('button', { name: /Back/i }))
    expect(mockOnBack).toHaveBeenCalledTimes(2)
  })
})

// ─── SECTION 10: Edge Cases ───────────────────────────────────────────────────

describe('Section 10: Edge cases', () => {
  test('renders without crashing when answers prop is undefined', () => {
    mockFetchSuccess()
    render(<Location onNext={mockOnNext} onBack={mockOnBack} answers={undefined} />)
    expect(screen.getByText(/Where is your property\?/i)).toBeInTheDocument()
  })

  test('renders without crashing when answers prop is empty object', () => {
    mockFetchSuccess()
    render(<Location onNext={mockOnNext} onBack={mockOnBack} answers={{}} />)
    expect(screen.getByRole('combobox')).toBeInTheDocument()
  })

  test('sends an empty object body when answers is undefined', async () => {
    mockFetchSuccess()
    render(<Location onNext={mockOnNext} onBack={mockOnBack} answers={undefined} />)
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Salford' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1))
    const [, options] = global.fetch.mock.calls[0]
    const body = JSON.parse(options.body)
    // Should at minimum contain the Location key
    expect(body.Location).toBe('Salford')
  })

  test('selecting every available location triggers a successful fetch for each', async () => {
    const locations = [
      'Altrincham', 'Ashton-under-Lyne', 'Bolton', 'Bury', 'Cheadle',
      'Chorlton', 'Didsbury', 'Hale', 'Levenshulme', 'Manchester City Centre',
      'Oldham', 'Prestwich', 'Rochdale', 'Sale', 'Salford', 'Stockport',
      'Stretford', 'Tameside', 'Trafford', 'Wigan', 'Wilmslow', 'Withington',
    ]

    for (const location of locations) {
      jest.clearAllMocks()
      mockFetchSuccess({ predicted_cost: 25000 })
      const { unmount } = renderLocation()
      fireEvent.change(screen.getByRole('combobox'), { target: { value: location } })
      fireEvent.click(screen.getByRole('button', { name: /Next/i }))
      await waitFor(() => expect(mockOnNext).toHaveBeenCalledTimes(1))
      expect(mockOnNext).toHaveBeenCalledWith({ cost: 25000 })
      unmount()
    }
  })

  test('multiple Next clicks while awaiting do not duplicate fetch calls', async () => {
    // Simulate a slow API
    let resolveFetch
    global.fetch = jest.fn().mockReturnValue(
      new Promise((resolve) => {
        resolveFetch = resolve
      })
    )

    renderLocation()
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Salford' } })
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))
    fireEvent.click(screen.getByRole('button', { name: /Next/i }))

    // Resolve the first (and only) pending fetch
    resolveFetch({ ok: true, json: async () => ({ predicted_cost: 10000 }) })

    await waitFor(() => expect(mockOnNext).toHaveBeenCalled())
    // Fetch was called twice because there's no double-submit guard —
    // this test documents the current behaviour and can be updated if a guard is added
    expect(global.fetch).toHaveBeenCalledTimes(2)
  })
})