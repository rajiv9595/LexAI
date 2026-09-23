import { PROTOTYPE_JURISDICTION } from '../types/research'
import type { ResearchSort, ResearchSourceType } from '../types/research'
import './ResearchFilters.css'

export type SourceTypeFilter = ResearchSourceType | 'all'

interface ResearchFiltersProps {
  sourceType: SourceTypeFilter
  jurisdiction: string
  sort: ResearchSort
  onSourceTypeChange: (value: SourceTypeFilter) => void
  onJurisdictionChange: (value: string) => void
  onSortChange: (value: ResearchSort) => void
}

function ResearchFilters({
  sourceType,
  jurisdiction,
  sort,
  onSourceTypeChange,
  onJurisdictionChange,
  onSortChange,
}: ResearchFiltersProps) {
  return (
    <div className="research-filters">
      <div className="research-filter-field">
        <label className="research-filter-label" htmlFor="research-filter-source">
          Source Type
        </label>
        <select
          id="research-filter-source"
          className="research-filter-select"
          value={sourceType}
          onChange={(event) =>
            onSourceTypeChange(event.target.value as SourceTypeFilter)
          }
        >
          <option value="all">All</option>
          <option value="statute">Statutes</option>
          <option value="case">Cases</option>
          <option value="precedent">Precedents</option>
          <option value="regulation">Regulations</option>
          <option value="general-reference">General References</option>
        </select>
      </div>
      <div className="research-filter-field">
        <label
          className="research-filter-label"
          htmlFor="research-filter-jurisdiction"
        >
          Jurisdiction
        </label>
        <select
          id="research-filter-jurisdiction"
          className="research-filter-select"
          value={jurisdiction}
          onChange={(event) => onJurisdictionChange(event.target.value)}
        >
          <option value="all">All</option>
          <option value={PROTOTYPE_JURISDICTION}>{PROTOTYPE_JURISDICTION}</option>
        </select>
      </div>
      <div className="research-filter-field">
        <label className="research-filter-label" htmlFor="research-filter-sort">
          Sort
        </label>
        <select
          id="research-filter-sort"
          className="research-filter-select"
          value={sort}
          onChange={(event) => onSortChange(event.target.value as ResearchSort)}
        >
          <option value="relevance">Relevance</option>
          <option value="date">Date</option>
        </select>
      </div>
    </div>
  )
}

export default ResearchFilters
