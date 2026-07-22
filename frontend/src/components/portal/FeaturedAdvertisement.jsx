import { ChevronRight, ExternalLink, MessageCircle } from "lucide-react";

import SmartCampaignMedia from "./SmartCampaignMedia";

export default function FeaturedAdvertisement({
  currentAd,
  ads,
  baseUrl,
  currentAdIndex,
  setCurrentAdIndex,
  showPreviousAd,
  showNextAd,
  hasRealAd,
  formatWhatsApp,
}) {
  if (!currentAd) {
    return null;
  }

  return (
    <section
      aria-labelledby="featured-ad-title"
      className="relative overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900"
    >
      <SmartCampaignMedia
        src={
          currentAd.media_url
            ? `${baseUrl}${currentAd.media_url}`
            : null
        }
        alt={currentAd.title}
        mediaType="image"
        mediaKey={currentAd.id}
        fallback={
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-blue-900 to-purple-900">
            <span className="text-2xl font-bold">
              {currentAd.title}
            </span>
          </div>
        }
      >
        {ads.length > 1 && (
          <div className="absolute inset-x-3 bottom-3 flex items-center justify-between gap-3">
            <button
              type="button"
              onClick={showPreviousAd}
              aria-label="Previous featured offer"
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-white/20 bg-black/50 text-white backdrop-blur transition hover:bg-black/70"
            >
              <ChevronRight className="h-5 w-5 rotate-180" />
            </button>

            <div className="flex items-center gap-3 rounded-full border border-white/10 bg-black/50 px-3 py-2 backdrop-blur">
              <span className="text-xs font-semibold text-white">
                {currentAdIndex + 1} / {ads.length}
              </span>

              <div className="flex items-center gap-2">
                {ads.map((ad, index) => (
                  <button
                    key={ad.id || index}
                    type="button"
                    onClick={() => setCurrentAdIndex(index)}
                    aria-label={`Show featured offer ${index + 1}`}
                    className={`h-2 rounded-full transition-all ${
                      index === currentAdIndex
                        ? "w-6 bg-white"
                        : "w-2 bg-white/40 hover:bg-white/70"
                    }`}
                  />
                ))}
              </div>
            </div>

            <button
              type="button"
              onClick={showNextAd}
              aria-label="Next featured offer"
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-white/20 bg-black/50 text-white backdrop-blur transition hover:bg-black/70"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        )}
      </SmartCampaignMedia>

      <div className="p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-blue-400">
              Featured Offer
            </p>
            <h2 id="featured-ad-title" className="mt-1 text-lg font-semibold">
              {hasRealAd
                ? currentAd.title
                : "Premium advertising placement"}
            </h2>
          </div>

          {!hasRealAd && (
            <span className="shrink-0 rounded-full border border-neutral-700 bg-neutral-800 px-3 py-1 text-xs text-neutral-400">
              Available
            </span>
          )}
        </div>

        <div className="mt-3 flex flex-wrap gap-3">
          {currentAd.whatsapp_number && (
            <a
              href={`https://wa.me/${formatWhatsApp(
                currentAd.whatsapp_number
              )}?text=Hi, I saw your ad on CAIWAVE WiFi`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 font-medium text-white transition-colors hover:bg-green-700"
            >
              <MessageCircle className="h-5 w-5" />
              Chat on WhatsApp
            </a>
          )}

          {currentAd.click_url && (
            <a
              href={currentAd.click_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-700"
            >
              <ExternalLink className="h-5 w-5" />
              Visit Website
            </a>
          )}
        </div>
      </div>
    </section>
  );
}
