export default function CampaignHero({ campaign, baseUrl }) {
  if (!campaign) {
    return null;
  }

  const campaignLabel =
    campaign.coverage_scope === "national"
      ? "National Campaign"
      : "Featured Campaign";

  return (
    <section
      aria-labelledby="featured-campaign-title"
      className="overflow-hidden rounded-xl border border-blue-700/40 bg-gradient-to-br from-blue-950/90 via-neutral-900 to-purple-950/80"
    >
      {campaign.image_url && (
        <div className="relative aspect-video w-full overflow-hidden bg-neutral-900">
          <img
            src={`${baseUrl}${campaign.image_url}`}
            alt={campaign.name || "CAIWAVE featured campaign"}
            className="h-full w-full object-cover"
          />

          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/10 to-transparent" />

          <div className="absolute left-4 top-4">
            <span className="rounded-full border border-white/20 bg-black/60 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-white backdrop-blur">
              {campaignLabel}
            </span>
          </div>
        </div>
      )}

      <div className="p-5">
        {!campaign.image_url && (
          <span className="mb-3 inline-flex rounded-full border border-blue-400/30 bg-blue-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-blue-200">
            {campaignLabel}
          </span>
        )}

        <h2
          id="featured-campaign-title"
          className="text-xl font-bold text-white sm:text-2xl"
        >
          {campaign.name}
        </h2>

        {campaign.description && (
          <p className="mt-2 leading-relaxed text-neutral-300">
            {campaign.description}
          </p>
        )}
      </div>
    </section>
  );
}
