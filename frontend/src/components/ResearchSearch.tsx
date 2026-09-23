import './ResearchSearch.css'

interface ResearchSearchProps {
  query: string
  onQueryChange: (value: string) => void
  onSearch: () => void
}

function ResearchSearch({ query, onQueryChange, onSearch }: ResearchSearchProps) {
  return (
    <form
      className="research-search-form"
      role="search"
      onSubmit={(event) => {
        event.preventDefault()
        onSearch()
      }}
    >
      <div className="research-search-field">
        <label className="sr-only" htmlFor="research-search-input">
          Describe a legal issue or research topic
        </label>
        <input
          id="research-search-input"
          className="research-search-input"
          type="search"
          value={query}
          placeholder="Describe a legal issue or research topic..."
          autoComplete="off"
          onChange={(event) => onQueryChange(event.target.value)}
        />
      </div>
      <button type="submit" className="btn btn-primary">
        Search
      </button>
    </form>
  )
}

export default ResearchSearch
