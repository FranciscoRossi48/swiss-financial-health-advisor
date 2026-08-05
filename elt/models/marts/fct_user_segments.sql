-- Final per-user segment assignment: joins each user's cluster (int_user_segments)
-- to the human-readable label computed for that cluster's centroid
-- (fct_segment_centroids). Mirrors the merge in fit_user_segments().

select
    s.user_id,
    s.profile,
    s.segment,
    c.segment_label
from {{ ref("int_user_segments") }} as s
inner join {{ ref("fct_segment_centroids") }} as c on s.segment = c.segment
