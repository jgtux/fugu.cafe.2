{-# LANGUAGE OverloadedStrings #-}

import Data.Bits (xor)
import Data.Char (ord)
import Data.Word (Word32)
import Hakyll
import Numeric (showHex)
import Text.Pandoc.Options (HTMLMathMethod (..), WriterOptions (..))

siteDescription :: String
siteDescription = "Technical notes on UNIX-based systems, networking, data, machine learning, privacy, programming, opinions and related topics."

-- MathML is rendered by the browser itself: no JavaScript, so it fits the
-- relayd Content-Security-Policy (default-src 'self', no inline scripts)
articleCompiler :: Compiler (Item String)
articleCompiler =
    pandocCompilerWith
        defaultHakyllReaderOptions
        defaultHakyllWriterOptions { writerHTMLMathMethod = MathML }

feedConfig :: FeedConfiguration
feedConfig = FeedConfiguration
    { feedTitle       = "Home"
    , feedDescription = siteDescription
    , feedAuthorName  = "João G."
    , feedAuthorEmail = "joao.guedes@posteo.com"
    , feedRoot        = "https://fugu.cafe"
    }

-- relayd sends max-age=86400: a new ?v= per stylesheet change makes
-- returning visitors fetch it instead of pairing new pages with old css
fnv1a :: String -> String
fnv1a = flip showHex "" . foldl step (2166136261 :: Word32)
  where
    step h c = (h `xor` fromIntegral (ord c)) * 16777619

cssVersionField :: Context a
cssVersionField = field "cssv" $ \_ -> fnv1a <$> loadBody "css/style.css"

postCtx :: Context String
postCtx =
    constField "root" "https://fugu.cafe" <>
    dateField "date" "%Y-%m-%d" <>
    cssVersionField <>
    defaultContext

feedCtx :: Context String
feedCtx =
    bodyField "description" <>
    postCtx

main :: IO ()
main = hakyll $ do
    match "images/**" $ do
        route idRoute
        compile copyFileCompiler

    -- browsers ask for /favicon.ico before reading any <link>
    match "images/icons/favicon.ico" $ version "root" $ do
        route $ constRoute "favicon.ico"
        compile copyFileCompiler

    match "fonts/*" $ do
        route idRoute
        compile copyFileCompiler

    match "css/*" $ do
        route idRoute
        compile compressCssCompiler

    match "articles/*.md" $ do
        route $ setExtension "html"
        compile $
            articleCompiler
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
                    constField "description" siteDescription <>
                    constField "root" "https://fugu.cafe" <>
                    constField "isHome" "true" <>
                    cssVersionField <>
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
