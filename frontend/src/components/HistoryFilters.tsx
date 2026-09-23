import type {
  HistoryItemType,
  HistorySort,
  HistoryStatus,
} from '../types/history'
import './HistoryFilters.css'

export type HistoryTypeFilter = HistoryItemType | 'all'
export type HistoryStatusFilter = HistoryStatus | 'all'

interface HistoryFiltersProps {
  type: HistoryTypeFilter
  status: HistoryStatusFilter
  sort: HistorySort
  onTypeChange: (value: HistoryTypeFilter) => void
  onStatusChange: (value: HistoryStatusFilter) => void
  onSortChange: (value: HistorySort) => void
  onClear: () => void
}

function HistoryFilters({
  type,
  status,
  sort,
  onTypeChange,
  onStatusChange,
  onSortChange,
  onClear,
}: HistoryFiltersProps) {
  return (
    <div className="history-filters">
      <div className="history-filter-field">
        <label className="history-filter-label" htmlFor="history-filter-type">
          Activity Type
        </label>
        <select
          id="history-filter-type"
          className="history-filter-select"
          value={type}
          onChange={(event) =>
            onTypeChange(event.target.value as HistoryTypeFilter)
          }
        >
          <option value="all">All Activity</option>
          <option value="assistant">Legal Assistant</option>
          <option value="document">Documents</option>
          <option value="research">Research</option>
        </select>
      </div>
      <div className="history-filter-field">
        <label className="history-filter-label" htmlFor="history-filter-status">
          Status
        </label>
        <select
          id="history-filter-status"
          className="history-filter-select"
          value={status}
          onChange={(event) =>
            onStatusChange(event.target.value as HistoryStatusFilter)
          }
        >
          <option value="all">All Status</option>
          <option value="prototype">Prototype</option>
          <option value="draft">Draft</option>
          <option value="completed">Completed</option>
        </select>
      </div>
      <div className="history-filter-field">
        <label className="history-filter-label" htmlFor="history-filter-sort">
          Sort
        </label>
        <select
          id="history-filter-sort"
          className="history-filter-select"
          value={sort}
          onChange={(event) => onSortChange(event.target.value as HistorySort)}
        >
          <option value="recent">Most Recent</option>
          <option value="oldest">Oldest</option>
          <option value="title">Title</option>
        </select>
      </div>
      <div>
        <button type="button" className="btn btn-ghost" onClick={onClear}>
          Clear Filters
        </button>
      </div>
    </div>
  )
}

export default HistoryFilters
