{-# LANGUAGE OverloadedStrings #-}

import Hakyll

feedConfig :: FeedConfiguration
feedConfig = FeedConfiguration
    { feedTitle       = "Home"
    , feedDescription = "Technical notes on UNIX-based systems, networking, privacy, programming, opinions and related topics."
    , feedAuthorName  = "João G."
    , feedAuthorEmail = "joao.guedes@posteo.com"
    , feedRoot        = "https://fugu.cafe"
    }

postCtx :: Context String
postCtx =
    constField "root" "https://fugu.cafe" <>
    dateField "date" "%Y-%m-%d" <>
    defaultContext

feedCtx :: Context String
feedCtx =
    bodyField "description" <>
    postCtx

main :: IO ()
main = hakyll $ do
    match "images/*" $ do
        route idRoute
        compile copyFileCompiler

    match "css/*" $ do
        route idRoute
        compile compressCssCompiler

    match "articles/*.md" $ do
        route $ setExtension "html"
        compile $
            pandocCompiler
                >>= saveSnapshot "content"
                >>= loadAndApplyTemplate "templates/post.html" postCtx
                >>= loadAndApplyTemplate "templates/default.html" postCtx
                >>= relativizeUrls

    create ["index.html"] $ do
        route idRoute
        compile $ do
            posts <- recentFirst =<< loadAll "articles/*.md"
            let indexCtx =
                    listField "posts" postCtx (return posts) <>
                    constField "title" "fugu.cafe" <>
                    constField "description" "Technical notes on UNIX-based systems, networking, privacy, programming, opinions and related topics." <>
                    constField "root" "https://fugu.cafe" <>
                    constField "isHome" "true" <>
                    defaultContext

            makeItem ""
                >>= loadAndApplyTemplate "templates/index.html" indexCtx
                >>= loadAndApplyTemplate "templates/default.html" indexCtx
                >>= relativizeUrls

    create ["rss.xml"] $ do
        route idRoute
        compile $ do
            posts <- fmap (take 10) . recentFirst =<<
                loadAllSnapshots "articles/*.md" "content"
            renderRss feedConfig feedCtx posts

    match "templates/*" $ compile templateBodyCompiler
