create function public.get_social_dashboard(p_days integer default 7) returns jsonb
language plpgsql security definer set search_path='' as $$
declare since timestamptz; begin
 -- Reuse the existing private-dashboard authorization, including its exact owner gate.
 perform public.get_growth_dashboard(p_days);
 if p_days not in (1,7,30) or p_days is null then p_days=7; end if;
 since=now()-make_interval(days=>p_days);
 return jsonb_build_object('days',p_days,
 'sources',(select coalesce(jsonb_agg(q),'[]') from (select metadata->>'source' label,count(*) value from public.growth_events where created_at>=since and event='social_landing' and metadata->>'source' in ('x','telegram') group by 1 order by 2 desc)q),
 'campaigns',(select coalesce(jsonb_agg(q),'[]') from (select (metadata->>'source')||' / '||(metadata->>'campaign') label,count(*) value from public.growth_events where created_at>=since and event='social_landing' and metadata->>'source' in ('x','telegram') group by 1 order by 2 desc limit 15)q),
 'actions',(select coalesce(jsonb_agg(q),'[]') from (select (metadata->>'source')||' / '||event label,count(*) value from public.growth_events where created_at>=since and event in ('newsletter_submit','affiliate_click') and metadata->>'source' in ('x','telegram') group by 1 order by 2 desc)q));
end $$;
revoke all on function public.get_social_dashboard(integer) from public,anon;
grant execute on function public.get_social_dashboard(integer) to authenticated;
