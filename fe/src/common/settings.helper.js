export const SettingsHelper = {
    getShowProxyTo() {
        return localStorage.showProxyTo ? localStorage.showProxyTo : defaultClientSettings.showProxyTo;
    },
    getShowAllTo() {
        return localStorage.showAllTo ? localStorage.showAllTo : defaultClientSettings.showAllTo;
    },
    getShowAllFrom() {
        return localStorage.showAllFrom ? localStorage.showAllFrom : defaultClientSettings.showAllFrom;
    },
}

const defaultClientSettings = {
    showProxyTo: true,
    showAllTo: false,
    showAllFrom: false,
    candidatesSorting: CANDIDATES_SORTING_NEAREST
}

export const CANDIDATES_SORTING_NEAREST = 'nearest'
export const CANDIDATES_SORTING_SIMILAR = 'similar'
