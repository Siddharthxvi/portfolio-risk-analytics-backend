import sys
import os

# Add parent dir to path so we can import from core and models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine, Base
import models

def init_db():
    print("Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

    print("Executing custom SQL for Triggers and Constraints...")
    with engine.begin() as conn:
        
        # 1. PORTFOLIO_ASSET Weight Validation
        conn.execute(text('''
        CREATE OR REPLACE FUNCTION check_portfolio_weight() RETURNS trigger AS $$
        DECLARE
            total_weight FLOAT;
        BEGIN
            SELECT COALESCE(SUM(weight), 0) INTO total_weight
            FROM portfolio_asset
            WHERE portfolio_id = NEW.portfolio_id;

            IF ABS(total_weight - 1.0) > 0.001 THEN
                RAISE EXCEPTION 'Portfolio weights must sum to 1.0 (currently %)', total_weight;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        '''))
        conn.execute(text('DROP TRIGGER IF EXISTS trg_check_portfolio_weight ON portfolio_asset;'))
        conn.execute(text('''
        CREATE CONSTRAINT TRIGGER trg_check_portfolio_weight
        AFTER INSERT OR UPDATE ON portfolio_asset
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE FUNCTION check_portfolio_weight();
        '''))

        # 2. SCENARIO Deletion Guard
        conn.execute(text('''
        CREATE OR REPLACE FUNCTION guard_scenario_deletion() RETURNS trigger AS $$
        BEGIN
            IF EXISTS (SELECT 1 FROM simulation_run WHERE scenario_id = OLD.scenario_id) THEN
                RAISE EXCEPTION 'Cannot delete a scenario that has associated simulation runs.';
            END IF;
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
        '''))
        conn.execute(text('DROP TRIGGER IF EXISTS trg_guard_scenario_deletion ON scenario;'))
        conn.execute(text('''
        CREATE TRIGGER trg_guard_scenario_deletion
        BEFORE DELETE ON scenario
        FOR EACH ROW
        EXECUTE FUNCTION guard_scenario_deletion();
        '''))

        # 3. SCENARIO Parameter Checks
        conn.execute(text('''
        CREATE OR REPLACE FUNCTION check_scenario_parameters() RETURNS trigger AS $$
        BEGIN
            IF NEW.volatility_multiplier <= 0 THEN
                RAISE EXCEPTION 'Volatility multiplier must be > 0.';
            END IF;
            IF NEW.equity_shock_pct < -1.0 OR NEW.equity_shock_pct > 1.0 THEN
                RAISE EXCEPTION 'Equity shock percentage must be between -1.0 and 1.0.';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        '''))
        conn.execute(text('DROP TRIGGER IF EXISTS trg_check_scenario_parameters ON scenario;'))
        conn.execute(text('''
        CREATE TRIGGER trg_check_scenario_parameters
        BEFORE INSERT OR UPDATE ON scenario
        FOR EACH ROW
        EXECUTE FUNCTION check_scenario_parameters();
        '''))

        # 4. RISK_METRIC Sanity Check
        conn.execute(text('''
        CREATE OR REPLACE FUNCTION check_risk_metric_sanity() RETURNS trigger AS $$
        DECLARE
            v95 FLOAT;
            v99 FLOAT;
            e95 FLOAT;
        BEGIN
            SELECT metric_value INTO v95 FROM risk_metric WHERE run_id = NEW.run_id AND metric_type = 'VaR_95';
            SELECT metric_value INTO v99 FROM risk_metric WHERE run_id = NEW.run_id AND metric_type = 'VaR_99';
            SELECT metric_value INTO e95 FROM risk_metric WHERE run_id = NEW.run_id AND metric_type = 'ES_95';

            IF v99 IS NOT NULL AND v95 IS NOT NULL AND v99 < v95 THEN
                RAISE EXCEPTION 'VaR_99 (%) must be >= VaR_95 (%)', v99, v95;
            END IF;

            IF e95 IS NOT NULL AND v95 IS NOT NULL AND e95 < v95 THEN
                RAISE EXCEPTION 'ES_95 (%) must be >= VaR_95 (%)', e95, v95;
            END IF;

            IF v95 IS NOT NULL AND v95 < 0 THEN
                RAISE EXCEPTION 'VaR_95 (%) must be >= 0', v95;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        '''))
        conn.execute(text('DROP TRIGGER IF EXISTS trg_check_risk_metric_sanity ON risk_metric;'))
        conn.execute(text('''
        CREATE CONSTRAINT TRIGGER trg_check_risk_metric_sanity
        AFTER INSERT ON risk_metric
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE FUNCTION check_risk_metric_sanity();
        '''))

    print("Triggers and Constraints initialized successfully.")

if __name__ == "__main__":
    init_db()
