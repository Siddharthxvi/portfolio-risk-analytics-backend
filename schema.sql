-- ============================================================
-- PORTFOLIO RISK ANALYTICS PLATFORM - FULL DATABASE SCHEMA
-- ============================================================

-- ================= CLEAN DROP =================
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS report CASCADE;
DROP TABLE IF EXISTS risk_metric CASCADE;
DROP TABLE IF EXISTS simulation_run CASCADE;
DROP TABLE IF EXISTS portfolio_benchmark CASCADE;
DROP TABLE IF EXISTS benchmark CASCADE;
DROP TABLE IF EXISTS portfolio_asset CASCADE;
DROP TABLE IF EXISTS portfolio CASCADE;
DROP TABLE IF EXISTS market_data CASCADE;
DROP TABLE IF EXISTS derivative CASCADE;
DROP TABLE IF EXISTS bond CASCADE;
DROP TABLE IF EXISTS equity CASCADE;
DROP TABLE IF EXISTS asset CASCADE;
DROP TABLE IF EXISTS asset_type CASCADE;
DROP TABLE IF EXISTS user_profile CASCADE;
DROP TABLE IF EXISTS user_role CASCADE;
DROP TABLE IF EXISTS role CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ================= USER =================
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- ================= USER PROFILE (1:1) =================
CREATE TABLE user_profile (
    profile_id SERIAL PRIMARY KEY,
    user_id INT UNIQUE REFERENCES users(user_id),
    full_name VARCHAR(100),
    phone VARCHAR(20),
    department VARCHAR(100),
    bio TEXT,
    avatar_url TEXT
);

-- ================= ROLE =================
CREATE TABLE role (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50),
    can_read BOOLEAN DEFAULT TRUE,
    can_write BOOLEAN DEFAULT FALSE,
    can_create BOOLEAN DEFAULT FALSE,
    can_delete BOOLEAN DEFAULT FALSE
);

-- ================= USER ROLE =================
CREATE TABLE user_role (
    user_id INT REFERENCES users(user_id),
    role_id INT REFERENCES role(role_id),
    assigned_at DATE,
    assigned_by INT REFERENCES users(user_id),
    PRIMARY KEY (user_id, role_id)
);

-- ================= ASSET TYPE =================
CREATE TABLE asset_type (
    type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(20) CHECK (
        type_name IN ('equity','bond','derivative', 'commodity')
    ),
    description TEXT,
    risk_category VARCHAR(20) CHECK (
        risk_category IN ('low','medium','high')
    )
);

-- ================= ASSET =================
CREATE TABLE asset (
    asset_id SERIAL PRIMARY KEY,
    type_id INT REFERENCES asset_type(type_id),
    ticker VARCHAR(20) UNIQUE NOT NULL,
    asset_name VARCHAR(100) NOT NULL,
    currency CHAR(3) NOT NULL,
    exchange VARCHAR(50),
    sector VARCHAR(50),
    country VARCHAR(50),
    base_price FLOAT NOT NULL CHECK (base_price > 0),
    annual_volatility FLOAT NOT NULL CHECK (annual_volatility > 0),
    annual_return FLOAT NOT NULL
);

-- ================= ISA SUBTYPES =================
CREATE TABLE equity (
    asset_id INT PRIMARY KEY REFERENCES asset(asset_id),
    dividend_yield FLOAT,
    market_cap_cat VARCHAR(20) CHECK (
        market_cap_cat IN ('large','mid','small')
    ),
    index_membership VARCHAR(50)
);

CREATE TABLE bond (
    asset_id INT PRIMARY KEY REFERENCES asset(asset_id),
    maturity_date DATE,
    coupon_rate FLOAT,
    bond_type VARCHAR(50) CHECK (
        bond_type IN ('government','corporate','municipal')
    ),
    credit_rating VARCHAR(20)
);

CREATE TABLE derivative (
    asset_id INT PRIMARY KEY REFERENCES asset(asset_id),
    underlying_asset_id INT REFERENCES asset(asset_id),
    expiry_date DATE,
    contract_type VARCHAR(20) CHECK (
        contract_type IN ('call','put','future','swap')
    ),
    strike_price FLOAT
);

-- ================= MARKET DATA =================
CREATE TABLE market_data (
    data_id SERIAL PRIMARY KEY,
    asset_id INT REFERENCES asset(asset_id),
    trading_date DATE NOT NULL,
    open_price FLOAT,
    close_price FLOAT NOT NULL,
    high_price FLOAT,
    low_price FLOAT,
    volume BIGINT,
    adjusted_close FLOAT
);

-- ================= PORTFOLIO =================
CREATE TABLE portfolio (
    portfolio_id SERIAL PRIMARY KEY,
    owner_id INT REFERENCES users(user_id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    base_currency VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) CHECK (
        status IN ('active','archived')
    )
);

-- ================= PORTFOLIO-ASSET =================
CREATE TABLE portfolio_asset (
    portfolio_id INT REFERENCES portfolio(portfolio_id),
    asset_id INT REFERENCES asset(asset_id),
    weight FLOAT NOT NULL CHECK (weight > 0 AND weight <= 1),
    quantity FLOAT NOT NULL CHECK (quantity > 0),
    purchase_price FLOAT,
    added_date DATE,
    removed_date DATE,
    PRIMARY KEY (portfolio_id, asset_id)
);

-- ================= BENCHMARK =================
CREATE TABLE benchmark (
    benchmark_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    description TEXT,
    benchmark_type VARCHAR(20) CHECK (
        benchmark_type IN ('equity','bond','blended')
    ),
    base_date DATE,
    currency VARCHAR(10)
);

-- ================= PORTFOLIO-BENCHMARK =================
CREATE TABLE portfolio_benchmark (
    portfolio_id INT REFERENCES portfolio(portfolio_id),
    benchmark_id INT REFERENCES benchmark(benchmark_id),
    assigned_at DATE,
    PRIMARY KEY (portfolio_id, benchmark_id)
);

-- ================= SCENARIO =================
CREATE TABLE scenario (
    scenario_id SERIAL PRIMARY KEY,
    created_by INT REFERENCES users(user_id),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    interest_rate_shock_bps INT NOT NULL CHECK (
        ABS(interest_rate_shock_bps) <= 1000
    ),
    volatility_multiplier FLOAT NOT NULL CHECK (volatility_multiplier > 0),
    equity_shock_pct FLOAT NOT NULL CHECK (
        equity_shock_pct BETWEEN -1 AND 1
    ),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- ================= SIMULATION RUN =================
CREATE TABLE simulation_run (
    run_id SERIAL PRIMARY KEY,
    portfolio_id INT NOT NULL REFERENCES portfolio(portfolio_id),
    scenario_id INT NOT NULL REFERENCES scenario(scenario_id),
    initiated_by INT REFERENCES users(user_id),
    run_type VARCHAR(20) NOT NULL CHECK (
        run_type IN ('monte_carlo','historical')
    ),
    status VARCHAR(20) CHECK (
        status IN ('pending','running','completed','failed')
    ),
    num_simulations INT NOT NULL CHECK (num_simulations BETWEEN 1000 AND 100000),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    execution_time_ms FLOAT,
    random_seed INT NOT NULL,
    time_horizon_days INT NOT NULL CHECK (time_horizon_days IN (1,10,252)),
    run_timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ================= RISK METRIC =================
CREATE TABLE risk_metric (
    run_id INT REFERENCES simulation_run(run_id) ON DELETE CASCADE,
    metric_type VARCHAR(20) CHECK (
        metric_type IN ('VaR_95','VaR_99','ES_95','volatility','max_drawdown')
    ),
    metric_value FLOAT NOT NULL,
    confidence_level FLOAT,
    computed_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (run_id, metric_type)
);

-- ================= REPORT =================
CREATE TABLE report (
    report_id SERIAL PRIMARY KEY,
    run_id INT REFERENCES simulation_run(run_id),
    generated_by INT REFERENCES users(user_id),
    title VARCHAR(100),
    generated_at TIMESTAMP DEFAULT NOW(),
    format VARCHAR(10) CHECK (
        format IN ('pdf','json','csv')
    ),
    summary TEXT
);

-- ================= AUDIT LOG =================
CREATE TABLE audit_log (
    log_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    entity_type VARCHAR(50) CHECK (
        entity_type IN ('portfolio','scenario','run','asset')
    ),
    entity_id INT,
    operation VARCHAR(20) CHECK (
        operation IN ('INSERT','UPDATE','DELETE')
    ),
    old_value TEXT,
    new_value TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    ip_address VARCHAR(50)
);

-- ================= INDEX =================
CREATE INDEX idx_simulation
ON simulation_run(portfolio_id, scenario_id);

-- ================= TRIGGER: RISK METRIC VALIDATION =================
CREATE OR REPLACE FUNCTION validate_risk_metrics()
RETURNS TRIGGER AS $$
DECLARE
    var_95 FLOAT;
    var_99 FLOAT;
    es_95 FLOAT;
BEGIN
    -- Fetch existing values for this run
    SELECT metric_value INTO var_95
    FROM risk_metric
    WHERE run_id = NEW.run_id AND metric_type = 'VaR_95';

    SELECT metric_value INTO var_99
    FROM risk_metric
    WHERE run_id = NEW.run_id AND metric_type = 'VaR_99';

    SELECT metric_value INTO es_95
    FROM risk_metric
    WHERE run_id = NEW.run_id AND metric_type = 'ES_95';

    -- Include NEW value being inserted/updated
    IF NEW.metric_type = 'VaR_95' THEN
        var_95 := NEW.metric_value;
    ELSIF NEW.metric_type = 'VaR_99' THEN
        var_99 := NEW.metric_value;
    ELSIF NEW.metric_type = 'ES_95' THEN
        es_95 := NEW.metric_value;
    END IF;

    -- Validation rules
    IF var_99 IS NOT NULL AND var_95 IS NOT NULL AND var_99 < var_95 THEN
        RAISE EXCEPTION 'VaR_99 must be >= VaR_95';
    END IF;

    IF var_95 IS NOT NULL AND var_95 < 0 THEN
        RAISE EXCEPTION 'VaR_95 must be >= 0';
    END IF;

    IF es_95 IS NOT NULL AND var_95 IS NOT NULL AND es_95 < var_95 THEN
        RAISE EXCEPTION 'ES_95 must be >= VaR_95';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trg_validate_risk_metrics
BEFORE INSERT OR UPDATE ON risk_metric
FOR EACH ROW
EXECUTE FUNCTION validate_risk_metrics();

-- ================= VIEWS =================
CREATE VIEW portfolio_summary AS
SELECT p.name, COUNT(pa.asset_id) AS total_assets
FROM portfolio p
LEFT JOIN portfolio_asset pa ON p.portfolio_id = pa.portfolio_id
GROUP BY p.name;

CREATE VIEW risk_dashboard AS
SELECT p.name AS portfolio, s.name AS scenario, rm.metric_type, rm.metric_value
FROM simulation_run sr
JOIN portfolio p ON sr.portfolio_id = p.portfolio_id
JOIN scenario s ON sr.scenario_id = s.scenario_id
JOIN risk_metric rm ON sr.run_id = rm.run_id;

-- ================= ROLES =================
-- CREATE ROLE dba_user LOGIN PASSWORD 'dba123';
-- CREATE ROLE analyst_user LOGIN PASSWORD 'analyst123';
-- CREATE ROLE viewer_user LOGIN PASSWORD 'viewer123';

-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO dba_user;
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO analyst_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO viewer_user;
-- GRANT SELECT ON portfolio_summary TO viewer_user;

CREATE TABLE user_settings (
    user_id integer NOT NULL PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    default_iterations integer NOT NULL DEFAULT 10000,
    default_horizon_days integer NOT NULL DEFAULT 252,
    default_confidence_level double precision NOT NULL DEFAULT 0.95
);
