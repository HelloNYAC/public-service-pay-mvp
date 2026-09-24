import SearchBar from "../components/SearchBar";
export default function HomePage() {
  return (
    <div className="container">
      <div className="hero">
        <h1>Public Service Pay Explorer</h1>
        <p>Search Government of Canada salary classifications and pay rates.</p>
        <SearchBar />
        <div className="section">
          <h3>Popular Searches</h3>
          <span className="badge">EC-04</span>
          <span className="badge">EC-05</span>
          <span className="badge">PM-05</span>
          <span className="badge">AS-01</span>
          <span className="badge">IT-03</span>
        </div>
      </div>
    </div>
  );
}