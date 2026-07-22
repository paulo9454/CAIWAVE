import SmartCampaignMedia from "./SmartCampaignMedia";

const resolveMediaUrl = (baseUrl, mediaUrl) => {
  if (!mediaUrl) {
    return "";
  }

  if (/^https?:\/\//i.test(mediaUrl)) {
    return mediaUrl;
  }

  return `${baseUrl}${mediaUrl}`;
};

export default function CampaignHero({ campaign, baseUrl }) {
  if (!campaign) {
    return null;
  }

  const assignedCreative = campaign.assigned_ads?.[0] || null;

  const mediaUrl =
    assignedCreative?.media_url || campaign.image_url || "";

  const mediaType =
    assignedCreative?.ad_type === "video" ? "video" : "image";

  const resolvedMediaUrl = resolveMediaUrl(baseUrl, mediaUrl);

  const mediaKey =
    assignedCreative?.id ||
    assignedCreative?.media_url ||
    campaign.id ||
    campaign.image_url;

  const campaignLabel =
    campaign.coverage_scope === "national"
      ? "National Campaign"
      : "Featured Campaign";

  return (
    <section
      aria-labelledby="featured-campaign-title"
      className="overflow-hidden rounded-xl border border-blue-700/40 bg-gradient-to-br from-blue-950/90 via-neutral-900 to-purple-950/80"
    >
      {resolvedMediaUrl && (
        <SmartCampaignMedia
          src={resolvedMediaUrl}
          alt={campaign.name || "CAIWAVE featured campaign"}
          mediaType={mediaType}
          mediaKey={mediaKey}
          autoPlay={mediaType === "video"}
          muted
          playsInline
          preload="metadata"
          controls={false}
        >
          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-black/45 to-transparent" />

          <div className="absolute left-4 top-4">
            <span className="rounded-full border border-white/20 bg-black/60 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-white backdrop-blur">
              {campaignLabel}
            </span>
          </div>
        </SmartCampaignMedia>
      )}

      <div className="p-5">
        {!resolvedMediaUrl && (
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
