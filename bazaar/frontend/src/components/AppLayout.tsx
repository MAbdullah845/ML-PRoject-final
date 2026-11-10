import { MarketDataProvider } from '../context/MarketDataContext';
import TopBar from './TopBar';
import TickerStrip from './TickerStrip';
import Watchlist from './Watchlist';
import Chart from './chart/Chart';
import SignalsPanel from './SignalsPanel';

export default function AppLayout() {
  return (
    <MarketDataProvider>
      <div className="app">
        <TopBar />
        <TickerStrip />
        <Watchlist />
        <Chart />
        <SignalsPanel />
      </div>
    </MarketDataProvider>
  );
}
