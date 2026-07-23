import {
  ExternalLink,
  ShoppingBag,
  Star,
} from "lucide-react";

import SmartCampaignMedia from "./SmartCampaignMedia";

const resolveUrl = (baseUrl, path) => {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  return `${baseUrl}${path}`;
};

const formatPrice = (value, currency = "KES") => {
  try {
    return new Intl.NumberFormat("en-KE", {
      style: "currency",
      currency,
      maximumFractionDigits: 2,
    }).format(Number(value || 0));
  } catch {
    return `${currency} ${Number(value || 0).toLocaleString("en-KE")}`;
  }
};

const MarketplacePanel = ({
  products = [],
  baseUrl,
}) => (
  <section
    id="marketplace"
    className="scroll-mt-5 rounded-[1.75rem] border border-white/10 bg-neutral-900/90 p-4 shadow-xl shadow-black/20 sm:p-5"
  >
    <div className="mb-4 flex items-start justify-between gap-4">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-purple-400">
          CAIMART Affiliate Market
        </p>

        <h2 className="mt-1 text-lg font-semibold text-white">
          Shop Partner Offers
        </h2>

        <p className="mt-1 text-sm text-neutral-400">
          Discover selected products from CAIWAVE merchant partners.
        </p>
      </div>

      {products.length > 1 && (
        <span className="shrink-0 rounded-full border border-purple-500/30 bg-purple-500/10 px-3 py-1 text-xs font-medium text-purple-300">
          Swipe
        </span>
      )}
    </div>

    {products.length === 0 ? (
      <div className="rounded-xl border border-dashed border-neutral-700 bg-neutral-950/50 px-5 py-10 text-center">
        <ShoppingBag className="mx-auto h-10 w-10 text-neutral-600" />
        <h3 className="mt-3 font-semibold text-white">
          New offers coming soon
        </h3>
        <p className="mt-1 text-sm text-neutral-500">
          CAIMART partner products will appear here.
        </p>
      </div>
    ) : (
      <>
        <div
          className="-mx-1 flex snap-x snap-mandatory gap-3 overflow-x-auto px-1 pb-3 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
          style={{ msOverflowStyle: "none" }}
        >
          {products.map((product) => {
            const imageUrl = resolveUrl(
              baseUrl,
              product.image_url
            );
            const visitUrl = resolveUrl(
              baseUrl,
              product.visit_url
            );

            return (
              <article
                key={product.id}
                className="min-w-[78%] snap-start overflow-hidden rounded-xl border border-neutral-700 bg-neutral-800 sm:min-w-[46%] md:min-w-[31%]"
              >
                {imageUrl ? (
                  <SmartCampaignMedia
                    src={imageUrl}
                    alt={product.name}
                    mediaType="image"
                    mediaKey={product.id}
                    fitMode="contain"
                    frameAspect="square"
                  >
                    <span className="absolute left-2 top-2 rounded-full border border-white/10 bg-black/65 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-white backdrop-blur">
                      {product.category}
                    </span>

                    {product.is_featured && (
                      <span className="absolute right-2 top-2 flex items-center gap-1 rounded-full bg-amber-400 px-2 py-1 text-[10px] font-bold uppercase text-black">
                        <Star className="h-3 w-3" />
                        Featured
                      </span>
                    )}
                  </SmartCampaignMedia>
                ) : (
                  <div className="relative aspect-square bg-gradient-to-br from-purple-950 via-indigo-900 to-blue-900">
                    <div className="flex h-full items-center justify-center">
                      <ShoppingBag className="h-14 w-14 text-white/50" />
                    </div>
                  </div>
                )}

                <div className="flex h-[240px] flex-col p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-purple-400">
                    {product.merchant_name}
                  </p>

                  <h3 className="mt-1 line-clamp-2 font-semibold text-white">
                    {product.name}
                  </h3>

                  <p className="mt-1 line-clamp-2 text-sm text-neutral-400">
                    {product.description}
                  </p>

                  <div className="mt-3 flex items-end gap-2">
                    <span className="font-bold text-green-400">
                      {formatPrice(
                        product.price,
                        product.currency
                      )}
                    </span>

                    {product.original_price != null && (
                      <span className="text-xs text-neutral-500 line-through">
                        {formatPrice(
                          product.original_price,
                          product.currency
                        )}
                      </span>
                    )}
                  </div>

                  <div className="mt-auto pt-4">
                    <a
                      href={visitUrl}
                      target="_blank"
                      rel="noopener noreferrer sponsored"
                      className="flex w-full items-center justify-center gap-2 rounded-lg bg-purple-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-purple-500"
                    >
                      View Merchant Offer
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </div>
                </div>
              </article>
            );
          })}
        </div>

        <div className="flex items-center justify-center gap-2 pt-2">
          {products.map((product, index) => (
            <span
              key={`marketplace-indicator-${product.id}`}
              className={`h-1.5 rounded-full ${
                index === 0
                  ? "w-6 bg-purple-400"
                  : "w-1.5 bg-neutral-600"
              }`}
            />
          ))}
        </div>
      </>
    )}

    <p className="pt-3 text-center text-xs leading-relaxed text-neutral-500">
      Affiliate disclosure: CAIWAVE may earn a commission when you
      visit or purchase from a partner. Prices and fulfilment are
      handled by the merchant.
    </p>
  </section>
);

export default MarketplacePanel;
