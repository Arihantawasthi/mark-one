-- Need to connect client table with issue table so that specific clients can be associated with specific issues/newsletters
CREATE TABLE IF NOT EXISTS client (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    password TEXT NOT NULL,

    is_active BOOLEAN DEFAULT TRUE,

    max_usage INT NOT NULL,
    current_usage INT DEFAULT 0,

    max_token_usage INT NOT NULL,
    current_token_usage INT DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analysis_run (
    id SERIAL PRIMARY KEY, -- maybe later client_id will be added as FK
    client_id INT REFERENCES client(id) ON DELETE CASCADE,
    display_title VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    notion_doc_url TEXT,
    niche TEXT,
    search_terms TEXT[],
    total_newsletters INT,
    total_issues INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS issue (
    id SERIAL PRIMARY KEY,
    newsletter VARCHAR(255) NOT NULL,
    analysis_run_id INT REFERENCES analysis_run(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    subtitle TEXT,
    author VARCHAR(255),
    canonical_url TEXT,
    published_date TIMESTAMP WITH TIME ZONE,
    content TEXT[] NOT NULL,
    like_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,
    links JSONB,
    toon TEXT NOT NULL,
    image_count INT DEFAULT 0,
    platform VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS issue_analytics (
    id SERIAL PRIMARY KEY,
    issue_id INT REFERENCES issue(id) ON DELETE CASCADE,
    title TEXT,
    subtitle TEXT,
    author VARCHAR(255),
    word_count INT,
    image_count INT,
    like_count INT,
    comment_count INT,
    section_count INT,
    emoji_count INT,
    title_emoji_count INT,
    subtitle_emoji_count INT,
    title_word_count INT,
    subtitle_word_count INT,
    addressed_user_by_name BOOLEAN,
    reading_time_minutes INT,
    product_mention_count INT,
    url TEXT,
    ctas JSONB,
    ads JSONB,
    overall_summary TEXT,
    overall_intent TEXT,
    overall_tone TEXT,
    platform VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS issue_aggregate_analytics (
    id SERIAL PRIMARY KEY,
    analysis_run_id INT REFERENCES analysis_run(id) ON DELETE CASCADE,

    avg_word_count FLOAT,
    avg_image_count FLOAT,
    avg_section_count FLOAT,
    avg_emoji_count FLOAT,
    avg_title_emoji_count FLOAT,
    avg_subtitle_emoji_count FLOAT,
    avg_title_word_count FLOAT,
    avg_subtitle_word_count FLOAT,
    reading_time_minutes FLOAT,
    overall_summary TEXT,
    overall_tone TEXT,
    overall_intent TEXT,
    engagement_graph JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE analysis_statuses (
    analysis_run_id BIGINT PRIMARY KEY
        REFERENCES analysis_run(id) ON DELETE CASCADE,
    statuses JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
