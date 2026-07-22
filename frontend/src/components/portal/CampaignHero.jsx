import { useState } from "react";
import { Maximize2 } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "../ui/dialog";
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
  const [previewOpen, setPreviewOpen] = useState(false);

  if (!campaign) {
    return null;
  }

  const assignedCreative = campaign.assigned_ads?.[0] || null;

  const mediaUrl =
    assignedCreative?.media_url ||
    campaign.media_url ||
    campaign.image_url ||
    "";

  const directMediaType =
    campaign.media_type === "video" ||
    /\.(mp4|webm)(\?.*)?$/i.test(campaign.media_url || "")
      ? "video"
      : "image";

  const mediaType = assignedCreative
    ? assignedCreative.ad_type === "video"
      ? "video"
      : "image"
    : directMediaType;

  const resolvedMediaUrl = resolveMediaUrl(baseUrl, mediaUrl);

  const mediaKey =
    assignedCreative?.id ||
    assignedCreative?.media_url ||
    campaign.media_url ||
    campaign.image_url ||
    campaign.id;

  const campaignLabel =
    campaign.coverage_scope === "national"
      ? "National Campaign"
      : "Featured Campaign";

  return (
    <>
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
          fitMode="contain"
          className="h-[220px] max-h-[220px] sm:h-[280px] sm:max-h-[280px]"
          autoPlay={mediaType === "video"}
          muted
          playsInline
          preload="metadata"
          controls={false}
        >
          {mediaType === "image" && (
            <>
              <button
                type="button"
                onClick={() => setPreviewOpen(true)}
                className="absolute inset-0 z-10 cursor-zoom-in"
                aria-label={`Expand ${campaign.name}`}
              >
                <span className="sr-only">
                  Open full-size campaign image
                </span>
              </button>

              <div className="pointer-events-none absolute right-3 top-3 z-20 flex h-9 w-9 items-center justify-center rounded-full border border-white/20 bg-black/60 text-white backdrop-blur">
                <Maximize2 className="h-4 w-4" />
              </div>
            </>
          )}

          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-black/45 to-transparent" />

          <div className="absolute left-4 top-4 z-20">
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

      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="w-[calc(100vw-2rem)] max-w-4xl border-white/10 bg-black/95 p-3 text-white">
          <DialogTitle className="sr-only">
            {campaign.name}
          </DialogTitle>

          {mediaType === "image" && resolvedMediaUrl && (
            <img
              src={resolvedMediaUrl}
              alt={campaign.name || "CAIWAVE featured campaign"}
              className="max-h-[85vh] w-full object-contain"
            />
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
